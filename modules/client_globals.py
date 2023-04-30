from typing import Dict
from . import storage

def init_db(server: str, port: str, op_name: str, imp_db: Dict[str, storage.Implant], lip: str, lport: str):
    global instance_db
    instance_db = storage.client_db(server=server, port=port, operator_name=op_name, imp_db=imp_db, lip=lip, lport=lport)
def init_listener():
    global listener_thread 
    listener_thread = 0


