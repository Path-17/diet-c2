from typing import Dict
from . import storage

def init(server: str, port: str, op_name: str, imp_db: Dict[str, storage.Implant]):
    global instance_db
    instance_db = storage.client_db(server=server, port=port, operator_name=op_name, imp_db=imp_db)

