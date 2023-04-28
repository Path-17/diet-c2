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
    return ""

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
