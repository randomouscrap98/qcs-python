
import json
import logging
import contentapi

# The entire config object with all defaults
config = {
    "api" : "https://oboy.smilebasicsource.com/api",
    "tokenfile" : ".qcstoken"
}

def main():
    print("Program start")
    logging.debug("Config: " + json.dumps(config, indent = 2))
    context = contentapi.ApiContext(config["api"])
    print("Program end")

# Because python reasons
if __name__ == "__main__":
    main()