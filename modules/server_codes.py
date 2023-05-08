from requests import Response
from enum import Enum
# The custom responses

# Types of ServerErrors for handling on client side
class ServerErrors(Enum):
    ERR_OPERATOR_NAME_EXISTS = "ERR_OPERATOR_NAME_EXISTS"
    ERR_LOGIN_EXCEPTION = "ERR_LOGIN_EXCEPTION"
    ERR_UPLOAD_EXCEPTION = "ERR_UPLOAD_EXCEPTION"
    ERR_IMPLANT_LOGIN_EXCEPTION = "ERR_IMPLANT_LOGIN_EXCEPTION"
    ERR_LOGOUT = "ERR_LOGOUT"

class ServerSuccess(Enum):
    UPLOAD_OK = "UPLOAD_OK"

# Types of ServerUpdates for TUI loggin
class ServerUpdates(Enum):
    NEW_IMPLANT = "NEW_IMPLANT"
    NEW_COMMAND_RESPONSE = "NEW_COMMAND_RESPONSE"
    IMPLANT_CHECKIN = "IMPLANT_CHECKIN"
    IMPLANT_DELETED = "IMPLANT_DELETED"

def handle_server_errors(response: Response):
    # Get the body of the response
    body = response.text

    # Match on ServerErrors value
    match body:
        case ServerErrors.ERR_OPERATOR_NAME_EXISTS.value:
            pass


