
import os
import json
import logging
import getpass
import textwrap
import threading
import re
import toml 
import readchar
import websocket
import win_unicode_console

from collections import OrderedDict
from colorama import Fore, Back, Style, init as colorama_init

import contentapi
import myutils

CONFIGFILE="config.toml"
MAXTITLE=25

# The entire config object with all defaults
config = {
    "api" : "http://localhost:5000/api",
    "default_loglevel" : "WARNING",
    "websocket_trace" : False,
    "default_room" : 0, # Zero means it will ask you for a room
    "expire_seconds" : 31536000, # 365 days in seconds, expiration for token
    "appear_in_global" : False,
    "tokenfile" : ".qcstoken"
}

# The command dictionary (only used to display help)
commands = OrderedDict([
    ("h", "Help, prints this menu!"),
    ("s", "Search, find and/or set a room to listen to (one at a time!)"),
    ("g", "Global userlist, print users using contentapi in general"),
    ("u", "Userlist, print users in the current room"),
    ("i", "Insert mode, allows you to send a message (pauses messages!)"),
    ("t", "Statistics, see info about runtime"),
    ("q", "Quit, no warning!")
])


def main():

    print("Program start")
    win_unicode_console.enable()
    colorama_init() # colorama init

    load_or_create_global_config()
    logging.info("Config: " + json.dumps(config, indent = 2))

    context = contentapi.ApiContext(config["api"], logging)
    logging.info("Testing connection to API at " + config["api"])
    logging.debug(json.dumps(context.api_status(), indent = 2))
    authenticate(config, context)

    # - Enter input loop, but check room number on "input" mode, don't let messages send in room 0
    #   - h to help
    #   - s to search rooms, enter #1234 to connect directly, empty string to quit
    #   - g to list global users
    #   - u to list users in room
    #   - i to input
    #   - q to quit entirely

    # Let users debug the websocket if they want I guess
    if config["websocket_trace"]:
        websocket.enableTrace(True)

    ws = websocket.WebSocketApp(context.websocket_endpoint())
    # Might as well reuse the websocket object for my websocket context data (oops, is that bad?)
    ws.context = context
    ws.user_info = context.user_me()
    ws.pause_output = False # Whether all output from the websocket should be paused (including status updates)
    ws.output_buffer = [] # Individual print statements buffered from output. 
    ws.main_config = config
    ws.current_room = 0
    ws.current_room_data = False
    ws.ignored = {}

    # Go out and get the default room if one was provided.
    if config["default_room"]:
        try:
            ws.current_room_data = context.get_by_id("content", config["default_room"])
            ws.current_room = config["default_room"]
            printr(Fore.GREEN + "Found default room %s" % ws.current_room_data["name"])
        except Exception as ex:
            printr(Fore.YELLOW + "Error searching for default room %d: %s" % (config["default_room"], ex))

    # set the callback functions
    ws.on_open = ws_onopen
    ws.on_close = ws_onclose
    ws.on_message = ws_onmessage

    ws.run_forever()

    print("Program end")


def ws_onclose(ws):
    print("Websocket closed! Program exit (FYI: you were in room %d)" % ws.current_room)
    exit()

def ws_onopen(ws):

    def main_loop():

        printr(Fore.GREEN + Style.BRIGHT + "\n-- Connected to live updates! --")

        if not ws.current_room:
            printr(Fore.YELLOW + "* You are not connected to any room! Press 'S' to search for a room! *")

        printstatus = True

        # The infinite input loop! Or something!
        while True:
            if printstatus:
                print_statusline(ws)

            printstatus = False         # Assume we are not printing the status every time (it's kinda annoying)
            ws.pause_output = False     # Allow arbitrary output again
            key = readchar.readkey()

            # # Oops, websocket is not connected but you asked for a command that requires websocket!
            # if not ws_context.connected and key in ["s", "g", "u", "i"]:
            #     print("No websocket connection")
            #     continue

            ws.pause_output = True      # Disable output for the duration of input handling

            if key == "h":
                for key, value in commands.items():
                    print(" " + Style.BRIGHT + key + Style.NORMAL + " - " + value)
            elif key == "s":
                search(ws)
                printstatus = True
            elif key == "g":
                ws.send(ws.context.gen_ws_request("userlist", id = "userlist_global"))
            elif key == "u":
                if not ws.current_room:
                    print("You're not in a room! Can't check userlist!")
                else:
                    # Just send it out, we have to wait for the websocket handler to get the response
                    ws.send(ws.context.gen_ws_request("userlist", id = "userlist_room_%d" % ws.current_room))
            elif key == "i":
                if not ws.current_room:
                    print("You're not in a room! Can't send messages!")
                else:
                    print("not yet")
                printstatus = True
            elif key == "t":
                print(" -- Ignored WS Data (normal) --")
                for key,value in ws.ignored.items():
                    printr(Style.BRIGHT + ("%16s" % key) + (" : %d" % value))
            elif key == "q":
                print("Quitting (may take a bit for the websocket to close)")
                ws.close()
                break

    # create a thread to run the blocking task
    thread = threading.Thread(target=main_loop)
    thread.start()

# Message handler for our websocket; will handle live messages for the room you're listening to and 
# userlist updates request results, but not much else (for now)
def ws_onmessage(ws, message):
    logging.debug("WSRCV: " + message)
    result = json.loads(message)

    # Someone asked for the userlist, check the id to figure out what to print and which list to see
    if result["type"] == "userlist":
        all_statuses = result["data"]["statuses"]
        if result["id"] == "userlist_global":
            usermessage = " -- Global userlist --"
            statuses = all_statuses["0"] if "0" in all_statuses else {}
        else: # This is a bad assumption, it should parse the room id out of the id instead (maybe?)
            usermessage = " -- Userlist for %s -- " % ws.current_room_data["name"]
            statuses = all_statuses[str(ws.current_room)] if str(ws.current_room) in all_statuses else {}
        print(usermessage)
        print_userlist(statuses, result["data"]["objects"]["user"])

    # Track ignored data
    if result["type"] not in ws.ignored:
        ws.ignored[result["type"]] = 0
    ws.ignored[result["type"]] += 1

# Print the plain userlist given a list of statuses (in a room or otherwise) and a list of user data
# (usually provided by whatever gave you the statuses)
def print_userlist(statuses, users):
    for key,value in statuses.items():
        key = int(key)
        user = contentapi.get_user_or_default(users,key)
        # Weird parenthesis are because I was aligning printed data before
        printr(Style.BRIGHT + "  " + ("%s" % (user["username"] + Style.DIM + " #%d" % key)) + Style.RESET_ALL + " - " + value)


# Loads the config from file into the global config var. If the file
# doesn't exist, the file is created from the defaults in config.
# The function returns nothing
def load_or_create_global_config():
    global config
    # Check if the config file exists
    if os.path.isfile(CONFIGFILE):
        # Read and deserialize the config file
        with open(CONFIGFILE, 'r', encoding='utf-8') as f:
            temp_config = toml.load(f)
            myutils.merge_dictionary(temp_config, config)
    else:
        # Serialize and write the config dictionary to the config file
        logging.warn("No config found at " + CONFIGFILE + ", creating now")
        with open(CONFIGFILE, 'w', encoding='utf-8') as f:
            toml.dump(config, f)

    myutils.set_logging_level(config["default_loglevel"])

# Enter a search loop which will repeat until you quit. Output should be PAUSED here 
# (but someone else does it for us, we don't even know what 'pausing' is)
def search(ws):
    while True:
        searchterm = input("Search text (#ROOMNUM = set room, # to quit): ")
        if searchterm == "#":
            return
        match = re.match(r'#(\d+)', searchterm)
        if match:
            roomid = int(match.group(1))
            try:
                ws.current_room_data = ws.context.get_by_id("content", roomid)
                ws.current_room = roomid
                print(Fore.GREEN + "Set room to %s" % ws.current_room_data["name"] + Style.RESET_ALL)
                return
            except Exception as ex:
                print(Fore.RED + "Couldn't find room with id %d" % roomid + Style.RESET_ALL)
        elif searchterm:
            # Go search for rooms and display them
            result = ws.context.basic_search(searchterm)["objects"]["content"]
            if len(result):
                for content in result:
                    printr(Style.BRIGHT + "%7s" % ("#%d" % content["id"]) + Style.RESET_ALL + " - %s" % content["name"])
            else:
                printr(Style.DIM + " -- No results -- ")

# Either pull the token from a file, or get the login from the command
# line if that doesn't work. WILL test your token against the real API
# even if it's pulled from file!
def authenticate(config, context: contentapi.ApiContext):
    message = "No token file found"
    if os.path.isfile(config["tokenfile"]):
        with open(config["tokenfile"], 'r') as f:
            token = f.read()
        logging.debug("Token from file: " + token)
        context.token = token
        if context.is_token_valid():
            logging.info("Logged in using token file " + config["tokenfile"])
            return
        else:
            message = "Token file expired"
    
    message += ", Please enter login for " + config["api"]

    while True:
        print(message)
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        try:
            token = context.login(username, password, config["expire_seconds"])
            with open(config["tokenfile"], 'w') as f:
                f.write(token)
            logging.info("Token accepted, written to " + config["tokenfile"])
            context.token = token
            return
        except Exception as ex:
            print("ERROR: %s" % ex)
            message = "Please try logging in again:"

def print_statusline(ws):
    # if ws_context.connected: bg = Back.GREEN else: bg = Back.RED
    if ws.current_room:
        name = ws.current_room_data["name"]
        room = "'" + (name[:(MAXTITLE - 3)] + '...' if len(name) > MAXTITLE else name) + "'"
    else:
        room = Fore.RED + Style.DIM + "NONE" + Style.NORMAL + Fore.BLACK
    print(Back.GREEN + Fore.BLACK + "\n " + ws.user_info["username"] + " - " + room + "  CTRL: h s g u i t q  " + Style.RESET_ALL)

# Print and then reset the style
def printr(msg):
    print(msg + Style.RESET_ALL)

# Because python reasons
if __name__ == "__main__":
    main()