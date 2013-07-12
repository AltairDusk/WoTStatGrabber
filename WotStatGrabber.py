import json
import urllib.request

USER_ID_REQ_PREFIX = 'http://api.worldoftanks.com/community/accounts/api/1.1/?source_token=WG-WoT_Assistant-1.3.2&search='
USER_ID_REQ_SUFFIX = '&offset=0&limit=1'

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class PlayerNotFoundError(Error):
    """Exception raised when a player cannot be found

    Attributes:
        player -- username that was looked up
        message -- explanation of the error
        
    """

    def __init__(self, player, message):
        self.player = player
        self.message = message

        
def request_user_id(userName):
    """Get the user ID from WG API given user name
    
    Keyword arguments:
    userName -- user to look up
    
    """
    
    # Build the URL and make the request to WG API.
    requestUrl = ''.join([USER_ID_REQ_PREFIX, userName, USER_ID_REQ_SUFFIX])
    response = urllib.request.urlopen(requestUrl, data=None)
    encoding = response.headers.get_content_charset()
    
    # Parse the JSON and get the user ID after
    # making sure we've found the correct user.
    userInfo = json.loads(response.read().decode(encoding))
    items = userInfo['data']['items']
    if len(items) > 1:
        raise PlayerNotFoundError(userName, 'Multiple players found')
    elif len(items) == 0 or items[0]['name'].lower() != userName.lower():   # Usernames are not case-sensitive for API requests
        raise PlayerNotFoundError(userName, 'Player was not found')
    else:
        userID = items[0]['id']
        
    return userID
