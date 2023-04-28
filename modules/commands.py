from typing import List
from . import client_globals
from . import client_errors

# This is the file that descibes the functions that handle client commands

def connected_to_implant() -> bool:
    if client_globals.instance_db.selected_implant == "":
        return False
    return True

# Command that selects an implant
def cmd_select(args: List[str], app):
    if len(args) > 1:
        raise client_errors.TooManyArguments
    if len(args) < 1:
        raise client_errors.TooFewArguments

    # Update the global selected implant
    client_globals.instance_db.selected_implant = args[0]

    # Update the border of command_output
    app.get_child_by_id("command_output").border_title = f"Command Output - Connected to {args[0]}"

    # Print a success message to the command Output
    app.get_child_by_id("command_output").print(f"Successfully connected to {args[0]}")

    return

# Command that sends a shell command to the server for an implant
def cmd_shell(args: List[str], app):
    # Error if not connected to an implant
    if not connected_to_implant():
        raise client_errors.NotConnectedToImplant
    # Error if there are no other args provided
    if len(args) < 1:
        raise client_errors.TooFewArguments

    implant_name = client_globals.instance_db.selected_implant

    # 
    return
# Command that sends a shellcode file to the server as well as a command
# The command is read first, and tells the implant where to pull the 
# shellcode file from on the server, reads it into memory, and executes
def cmd_shellcode_inject(args: List[str], app):
    return
# Different method of shellcode injection, this creates a process and injects it
# into it, same client -> server -> implant transfer method as shellcode_inject
def cmd_shellcode_spawn(args: List[str], app):
    return

# All associated server commands
def cmd_server(args: List[str], app):
    return

# Exits the client, the suplimentary args should be empty
def cmd_exit(args: List[str], app):
    return

# Here is the dict of supported commands 
CMD_TABLE = {
                "server": cmd_server,
                "exit": cmd_exit,
                "select": cmd_select,
                "shell": cmd_shell,
                "shellcode-inject": cmd_shellcode_inject,
                "shellcode-spawn": cmd_shellcode_spawn,
}

