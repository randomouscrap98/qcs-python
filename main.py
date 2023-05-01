
import os
import json
import logging
import contentapi
import toml
import myutils

CONFIGFILE="config.toml"

# The entire config object with all defaults
config = {
    "api" : "https://oboy.smilebasicsource.com/api",
    "expire_seconds" : 31536000, # 365 days in seconds, expiration for token
    "tokenfile" : ".qcstoken"
}

def main():
    print("Program start")
    load_or_create_global_config()
    logging.debug("Config: " + json.dumps(config, indent = 2))
    context = contentapi.ApiContext(config["api"], logging)
    print("Program end")

# Loads the config from file into the global config var. If the file
# doesn't exist, the file is created from the defaults in config.
# The function returns nothing
def load_or_create_global_config():
    global config
    # Check if the config file exists
    if os.path.exists(CONFIGFILE):
        # Read and deserialize the config file
        with open(CONFIGFILE, 'r', encoding='utf-8') as f:
            config = toml.load(f)
    else:
        # Serialize and write the config dictionary to the config file
        logging.warn("No config found at " + CONFIGFILE + ", creating now")
        with open(CONFIGFILE, 'w', encoding='utf-8') as f:
            toml.dump(config, f)


# Because python reasons
if __name__ == "__main__":
    main()