
# Used for custom client errors, like if you are not connected to a implant
# and try to run a shell command

# This file also includes the error handling functions that return the string
# to print when it is caught

class NotConnectedToImplant(Exception):
    pass
class TooManyArguments(Exception):
    pass
class TooFewArguments(Exception):
    pass
