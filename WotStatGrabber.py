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
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

        
def request_user_id(userName):
    requestUrl = ''.join([USER_ID_REQ_PREFIX, userName, USER_ID_REQ_SUFFIX])
    response = urllib.request.urlopen(requestUrl, data=None)
    encoding = response.headers.get_content_charset()
    userInfo = json.loads(response.read().decode(encoding))
    items = userInfo['data']['items']
    if len(items) > 1:
        raise PlayerNotFoundError(userName, 'Multiple players found')
    elif len(items) == 0 or items[0]['name'].lower() != userName.lower():   #Usernames are not case-sensitive for API requests
        raise PlayerNotFoundError(userName, 'Player was not found')
    else:
        userID = items[0]['id']
    return userID
