
import os
import json
import logging
import toml
import getpass

import contentapi
import myutils

CONFIGFILE="config.toml"

# The entire config object with all defaults
config = {
    "api" : "https://oboy.smilebasicsource.com/api",
    "default_loglevel" : "WARNING",
    "expire_seconds" : 31536000, # 365 days in seconds, expiration for token
    "tokenfile" : ".qcstoken"
}

def main():
    print("Program start")
    load_or_create_global_config()
    logging.info("Config: " + json.dumps(config, indent = 2))
    context = contentapi.ApiContext(config["api"], logging)
    logging.info("Testing connection to API at " + config["api"])
    logging.debug(json.dumps(context.api_status(), indent = 2))
    authenticate(config, context)
    print("Program end")

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


# Because python reasons
if __name__ == "__main__":
    main()