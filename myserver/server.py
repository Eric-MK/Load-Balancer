# Import necessary modules
from flask import Flask, jsonify
import os

# Initialize Flask application
app = Flask(__name__)

# Retrieve server side ID from an environment variable
server_id = os.getenv('SERVER_ID', '1')  # default to '1' if not set

# Define route for the home page
@app.route('/home', methods=['GET'])
def home():
    # Return a JSON response with a greeting message and the server ID
    return jsonify(message=f"Hello from Server: {server_id}", status="successful"), 200

# Define route for heartbeat check
@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    # Return an empty response with a 200 status code
    return '', 200  

# Run the Flask application if this script is executed directly
if __name__ == '__main__':
    # Start the server, listening on all available interfaces on port 5000
    app.run(host='0.0.0.0', port=5000)