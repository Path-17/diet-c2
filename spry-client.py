import argparse
from typing import Dict
from modules import tui
from modules import client_globals
from modules import server_codes
from os import _exit
import requests

def parse_initial_arguments():
    parser = argparse.ArgumentParser(
            prog='Spry-C2 Operator Client',
            description='Operator client for the Spry command and control framework')
    parser.add_argument('--server', help="The IP or domain of the C1.5 server you want to connect to.", required=True)
    parser.add_argument('--rport', help="The port of the C1.5 server you want to connect to.", required=True)
    parser.add_argument('--username', help="The username you want to login to the C1.5 server as", required=True)
    parser.add_argument('--lip', help="The IP you want the client to listen on for updates from the server", required=True)
    parser.add_argument('--lport', help="The port you want the client to listen on for updates from the server", required=True)
    args = parser.parse_args()
    return args

def login(server: str, port: str, name: str, op_ip: str, op_port: str) -> Dict:
    data = {'username': name, "lip": op_ip, "lport": op_port}
    login_endpoint = "/admin/login"

    try:
        x = requests.post(server+":"+port+login_endpoint, json=data)
        # Handle the operator exists error
        if x.text == server_codes.ServerErrors.ERR_OPERATOR_NAME_EXISTS.value:
            print(f"The operator \'{name}\' already exists on the supplied server, please pick a different one.")            
            _exit(1)
        return x.json()["implant_db"]
    except:
        print("Not able to connect to the server, please verify the URL:port is correct and that the server is online.\nExiting now...")
        _exit(1)

if __name__ == "__main__":
    args = parse_initial_arguments()
    # init the globals
    operator_name = args.username
    server = "http://"+args.server
    port = args.rport
    listen_port = args.lport
    listen_ip = args.lip

    # Attempt to sign in to the server with a POST request
    # the login function returns the implant_db data currently
    # on the server
    imp_db = login(server, port, operator_name, listen_ip, listen_port)
    
    # create the globals
    client_globals.init(server=server, port=port, op_name=operator_name, imp_db=imp_db)

    # load the TUI
    app = tui.Client()
    
    # start the listener 
    # server_thread = threading.Thread(target=lambda: listener.run(host=listen_ip, port=listen_port, debug=False, use_reloader=False)).start()

    # start the client TUI
    app.run()