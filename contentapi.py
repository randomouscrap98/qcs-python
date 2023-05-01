
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
    

    # Generate the standard headers we use for most requests. You usually don't need to
    # change anything here, just make sure your token is set if you want to be logged in
    def gen_header(self, content_type = "application/json"):
        headers = {
            "Content-Type" : content_type,
            "Accept" : content_type
        }
        if self.token:
            headers["Authorization"] = "Bearer" + self.token
        return headers
    
    # Given a standard response from the API, parse the status code to throw the appropriate
    # exceptions, or return the actual response from the API as a parsed object.
    def parse_response(self, response):
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            raise BadRequestError("Bad request: %s" % response.content)
        elif response.status_code == 401:
            raise AuthenticationError("Your token is bad!")
        elif response.status_code == 404:
            raise NotFoundError("Could not find content!")
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

    # Connect to the API to determine if your token is still valid. 
    def is_token_valid(self):
        try:
            return self.token and self.get("user/me")
        except Exception as ex:
            self.logger.debug("Error from endpoint: %s" % ex)
            return False


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