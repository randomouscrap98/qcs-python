
import requests
import logging

class AuthenticationError(Exception):
    """ Exception for 401 errors, meaning your token was bad (expired maybe?) """

class BadRequestError(Exception):
    """Exception for 400 errors, meaning you gave something funky to the API
       (maybe your search was malformed?) """

class NotFoundError(Exception):
    """Exception for 404 errors, meaning whatever you were looking for wasn't found
       (This is rare from the API) """

# Your gateway to the static endpoints for contentapi. It's a context because it needs
# to track stuff like "which api am I contacting" and "which user am I authenticating as (if any)"
class ApiContext:

    # You MUST define the endpoint when creating the API context! You can optionally set
    # the token on startup, or you can set it at any time. Set to a "falsey" value to 
    # to browse as an anonymous user
    def __init__(self, endpoint: str, logger: logging.Logger, token = False):
        self.endpoint = endpoint
        self.logger = logger
        self.token = token
    

    # Contentapi websocket endpoint is always wss, and we assume the websocket is always secure too.
    # If these are not reasonable assumptions... I guess make a regex replacement instead?
    def websocket_endpoint(self, lastId = 0):
        if not self.token:
            raise Exception("Cannot connect to websocket endpoint without token!!")
        result = self.endpoint.replace("https:", "wss:") + "/live/ws?token=%s" % self.token
        if lastId:
            result += "&lastId=%d" % lastId
        return result

    # Generate the standard headers we use for most requests. You usually don't need to
    # change anything here, just make sure your token is set if you want to be logged in
    def gen_header(self, content_type = "application/json"):
        headers = {
            "Content-Type" : content_type,
            "Accept" : content_type
        }
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        return headers
    
    # Given a standard response from the API, parse the status code to throw the appropriate
    # exceptions, or return the actual response from the API as a parsed object.
    def parse_response(self, response):
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            raise BadRequestError("Bad request: %s" % response.text)
        elif response.status_code == 401:
            raise AuthenticationError("Your token is bad!")
        elif response.status_code == 404:
            raise NotFoundError("Not found: %s" % response.text)
        else:
            raise Exception("Unknown error (%s) - %s" % (response.status_code, response.content))
    
    # Perform a standard get request and return the pre-parsed object (all contentapi endpoints
    # return objects). Throws exception on error
    def get(self, endpoint):
        url = self.endpoint + "/" + endpoint
        # self.logger.debug("GET: " + url) # Not necessary, DEBUG in requests does this
        response = requests.get(url, headers = self.gen_header())
        return self.parse_response(response)
    
    def post(self, endpoint, data):
        url = self.endpoint + "/" + endpoint
        # self.logger.debug("POST: " + url)
        response = requests.post(url, headers = self.gen_header(), json = data)
        return self.parse_response(response)

    # Connect to the API to determine if your token is still valid. Or, if you pass a token,
    # check if only the given token is valid
    def is_token_valid(self):
        try:
            return self.token and self.user_me()
        except Exception as ex:
            self.logger.debug("Error from endpoint: %s" % ex)
            return False


    # Return info about the current user based on the token. Useful to see if your token is valid
    # and who you are
    def user_me(self):
        return self.get("user/me")

    # Basic login endpoint, should return your token on success
    def login(self, username, password, expire_seconds = False):
        data = {
            "username" : username,
            "password" : password
        }
        if expire_seconds:
            data["expireSeconds"] = expire_seconds
        return self.post("user/login", data)

    # Get information about the API. Very useful to test your connection to the API
    def api_status(self):
        return self.get("status")
    
    # Access the raw search endpoint of the API (you must construct the special contentapi request yourself!)
    def search(self, requests):
        return self.post("request", requests)
    
    # A very basic search for outputting to the console. Constructs the contentapi search request for you: many assumptions are made!
    def basic_search(self, searchterm, limit = 0):
        return self.search({
            "values": {
                "searchterm": searchterm,
                "searchtermlike": "%" + searchterm + "%"
            },
            "requests": [{
                "type": "content",
                "fields": "~text,engagement", # All fields EXCEPT text and engagement
                "query": "name LIKE @searchtermlike",
                "order": "lastActionDate_desc",
                "limit": limit
            }]
        })
    
    # Return the singular item of 'type' for the given ID. Raises a "NotFoundError" if nothing found.
    def get_by_id(self, type, id, fields = "*"):
        result = self.search({
            "values" : {
                "id" : id
            },
            "requests": [{
                "type" : type,
                "fields": fields,
                "query": "id = @id"
            }]
        })

        things = result["objects"][type]
        if not len(things):
            raise NotFoundError("Couldn't find %s with id %d" % (type, id))
        return things[0]