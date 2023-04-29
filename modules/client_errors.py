from typing import List
# Used for custom client errors, like if you are not connected to a implant
# and try to run a shell command

# This file also includes the error handling functions that return the string
# to print when it is caught

class ImplantDoesntExist(Exception):
    pass
class CommandDoesntExist(Exception):
    pass
class NotConnectedToImplant(Exception):
    pass
class TooManyArguments(Exception):
    pass
class TooFewArguments(Exception):
    pass

def arg_len_error(args: List[str], max: int, min: int):
    if len(args) > max:
        raise TooManyArguments
    elif len(args) < min:
        raise TooFewArguments
    return
