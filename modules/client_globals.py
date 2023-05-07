from typing import Dict
from . import storage
from . import encryption

def init_db(server: str, port: str, op_name: str, imp_db: Dict[str, storage.Implant], lip: str, lport: str):
    global instance_db
    instance_db = storage.client_db(server=server, port=port, operator_name=op_name, imp_db=imp_db, lip=lip, lport=lport)
def init_listener():
    global listener_thread 
    listener_thread = 0
def init_logout_code():
    global logout_code
    logout_code = encryption.id_generator(N=32)


