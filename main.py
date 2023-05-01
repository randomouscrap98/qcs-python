
import os
import json
import logging
import getpass
import textwrap
import threading
import toml 
import readchar
import websocket

from collections import OrderedDict
from colorama import Fore, Back, Style, init as colorama_init

import contentapi
import myutils

CONFIGFILE="config.toml"

# The entire config object with all defaults
config = {
    "api" : "https://oboy.smilebasicsource.com/api",
    "default_loglevel" : "WARNING",
    "websocket_trace" : False,
    "default_room" : 0, # Zero means it will ask you for a room
    "expire_seconds" : 31536000, # 365 days in seconds, expiration for token
    "appear_in_global" : False,
    "tokenfile" : ".qcstoken"
}

commands = OrderedDict([
    ("h" , "Help, prints this menu!"),
    ("s" , "Search, find and/or set a room to listen to (one at a time!)"),
    ("g" , "Global userlist, print users using contentapi in general"),
    ("u" , "Userlist, print users in the current room"),
    ("i" , "Insert mode, allows you to send a message (pauses messages!)"),
    ("q" , "Quit, no warning!")
])


def main():

    print("Program start")
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
    ws.user_info = context.user_me()
    ws.current_room = config["default_room"]
    ws.pause_output = False # Whether all output from the websocket should be paused (including status updates)
    ws.output_buffer = [] # Individual print statements buffered from output. 
    ws.main_config = config

    # set the callback functions
    ws.on_open = ws_onopen
    ws.on_close = ws_onclose
    ws.on_message = ws_onmessage

    # connect to the WebSocket server and block until connected
    ws.run_forever()

    print("Program end")


def ws_onclose(ws):
    print("Websocket closed! Program exit (FYI: you were in room %d)" % ws.current_room)
    exit()

def ws_onopen(ws):

    def main_loop():
        printstatus = True

        print(Fore.GREEN + Style.BRIGHT + "\n-- Connected to live updates! --" + Style.RESET_ALL)

        # TODO: check to see if the id is a valid room
        if not ws.current_room:
            print(Fore.YELLOW + "* You are not connected to any room! Press 'S' to search for a room! *" + Style.RESET_ALL)

        # The infinite input loop! Or something!
        while True:
            if printstatus:
                print_statusline(ws)
            printstatus = True
            key = readchar.readkey()

            # # Oops, websocket is not connected but you asked for a command that requires websocket!
            # if not ws_context.connected and key in ["s", "g", "u", "i"]:
            #     print("No websocket connection")
            #     continue

            if key == "h":
                for key, value in commands.items():
                    print(" " + Style.BRIGHT + key + Style.NORMAL + " - " + value)
            elif key == "s":
                print("not yet")
            elif key == "g":
                print("not yet")
            elif key == "u":
                if not ws.current_room:
                    print("You're not in a room! Can't check userlist!")
                else:
                    print("not yet")
            elif key == "i":
                if not ws.current_room:
                    print("You're not in a room! Can't send messages!")
                else:
                    print("not yet")
            elif key == "q":
                print("Quitting (may take a bit for the websocket to close)")
                ws.close()
                break
            else:
                printstatus = False

    # create a thread to run the blocking task
    thread = threading.Thread(target=main_loop)
    thread.start()

def ws_onmessage(ws, message):
    pass


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
    print(Back.GREEN + Fore.BLACK + "\n User: " + ws.user_info["username"] + "  CTRL: h s g u i q  " + Style.RESET_ALL)

# Because python reasons
if __name__ == "__main__":
    main()