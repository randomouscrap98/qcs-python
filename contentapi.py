
import requests

# Exception for 401 errors, meaning your token was bad (expired maybe?)
class AuthenticationError(Exception):
    pass

# Exception for 400 errors, meaning you gave something funky to the API
# (maybe your search was malformed?)
class BadRequestError(Exception):
    pass

# Exception for 404 errors, meaning whatever you were looking for wasn't found
# (This is rare from the API)
class NotFoundError(Exception):
    pass

# Your gateway to the static endpoints for contentapi. It's a context because it needs
# to track stuff like "which api am I contacting" and "which user am I authenticating as (if any)"
class ApiContext:

    # You MUST define the endpoint when creating the API context! You can optionally set
    # the token on startup, or you can set it at any time. Set to a "falsey" value to 
    # to browse as an anonymous user
    def __init__(self, endpoint, logger, token = False):
        self.endpoint = endpoint
        self.logger = logger
        self.token = token
    
    # Generate the standard headers we use for most requests. You usually don't need to
    # change anything here, just make sure your token is set if you want to be logged in
    def gen_header(self, content_type = "application/json"):
        headers = {
            "Content-Type" : content_type
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    # Given a standard response from the API, parse the status code to throw the appropriate
    # exceptions, or return the actual response from the API as a parsed object.
    def parse_response(self, response):
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            raise BadRequestError(f"Bad request: {response.content}")
        elif response.status_code == 401:
            raise AuthenticationError("Your token is bad!")
        elif response.status_code == 404:
            raise NotFoundError("Could not find content!")
        else:
            raise Exception(f"Unknown error ({response.status_code}) - {response.content}")
    
    # Perform a standard get request and return the pre-parsed object (all contentapi endpoints
    # return objects). Throws exception on error
    def get(self, endpoint):
        response = requests.get(self.endpoint + "/" + endpoint, headers = self.gen_header())
        return self.parse_response(response)

    # Connect to the API to determine if your token is still valid. 
    def is_token_valid(self):
        try:
            return self.token and self.get("user/me")
        except Exception as ex:
            self.logger.debug(f"Error from endpoint: {ex}")
            return False

