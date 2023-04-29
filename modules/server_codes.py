from requests import Response
from enum import Enum
# The custom responses

class ServerErrors(Enum):
    ERR_OPERATOR_NAME_EXISTS = "ERR_OPERATOR_NAME_EXISTS"
    ERR_LOGIN_EXCEPTION = "ERR_LOGIN_EXCEPTION"

def handle_server_errors(response: Response):
    # Get the body of the response
    body = response.text

    # Match on ServerErrors value
    match body:
        case ServerErrors.ERR_OPERATOR_NAME_EXISTS.value:
            pass

