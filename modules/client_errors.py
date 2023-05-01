from typing import List
from rich.text import Text
# Used for custom client errors, like if you are not connected to a implant
# and try to run a shell command

# Helper to print error messages to command_output window
def print_err(app, text):
    app.get_widget_by_id("command_output").err_generic(text)

# This file also includes the error handling functions that return the string
# to print when it is caught

class ImplantDoesntExist(Exception):
    pass
def handle_ImplantDoesntExist(args: List[str], app):
    # Implant would be the second arg passed
    print_err(app, Text().assemble("The selected implant ", (args[1], "bold"), " doesn't exist"))
class CommandDoesntExist(Exception):
    pass
def handle_CommandDoesntExist(args: List[str], app):
    # Command doesn't exist, just print it to screen with an error
    #print_err(app, f"ERROR: The command \'{' '.join(args)}\' doesn't exist.")
    print_err(app, Text().assemble("The command \'", (' '.join(args), "bold"), "\' doesn't exist"))
class NotConnectedToImplant(Exception):
    pass
def handle_NotConnectedToImplant(args: List[str], app):
    # Not connected to implant, simply print error with suggestion to select one first
    #print_err(app, f"ERROR: No implant selected, please run \'select IMPLANT_NAME\' first.")
    print_err(app, Text().assemble("No implant selected, please run \'", ("select IMPLANT_NAME", "bold"), "\' first."))
class TooManyArguments(Exception):
    pass
def handle_TooManyArguments(args: List[str], app):
    # Print too many args
    #print_err(app, f"ERROR: Too many arguments supplied for the \'{args[0]}\' command.")
    print_err(app, Text().assemble("Too many arguments supplied for the \'", (args[0], "bold"), "\' command."))

class TooFewArguments(Exception):
    pass
def handle_TooFewArguments(args: List[str], app):
    #print_err(app, f"ERROR: Too few arguments supplied for the \'{args[0]}\' command.")
    print_err(app, Text().assemble("Too few arguments supplied for the \'", (args[0], "bold"), "\' command."))
class FileDoesntExist(Exception):
    pass
def handle_FileDoesntExist(args: List[str], app):
    # File name will be the second arg
    #print_err(app, f"ERROR: The provided file \'{args[1]}\' doesn't exist.")
    print_err(app, Text().assemble("The provided file \'", (args[1], "bold"), "\' doesn't exist."))
class UploadFailure(Exception):
    pass
def handle_UploadFailure(args: List[str], app):
    # TODO: Implement file upload retries
    #print_err(app, f"ERROR: The upload of file \'{args[1]}\' failed, no file was sent to the server.")
    print_err(app, Text().assemble("The upload of file \'", (args[1], "bold"), "\' failed, no file was sent to the server or implant."))

# Helper for arg lengths
def arg_len_error(args: List[str], max: int, min: int):
    if len(args) > max:
        raise TooManyArguments
    elif len(args) < min:
        raise TooFewArguments
    return

# Error handling table, points to the function for how to handle it
ERROR_TABLE = {
        ImplantDoesntExist: handle_ImplantDoesntExist,
        CommandDoesntExist: handle_CommandDoesntExist,
        NotConnectedToImplant: handle_NotConnectedToImplant,
        TooManyArguments: handle_TooManyArguments,
        TooFewArguments: handle_TooFewArguments,
        FileDoesntExist: handle_FileDoesntExist,
        UploadFailure: handle_UploadFailure,
        KeyError: handle_CommandDoesntExist
    }

