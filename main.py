
import json
import logging

# The entire config object with all defaults
config = {
    "api" : "https://oboy.smilebasicsource.com/api"
}

def main():
    print("Program start")
    logging.debug("Config: " + json.dumps(config, indent = 2))
    print("Program end")