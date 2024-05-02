from flask import Flask, jsonify
import os

app = Flask(__name__)

#Retrieve server side ID from an environment variable
server_id = os.getenv('SERVER_ID', '1')  #default to 1 if not set

@app.route('/home', methods=['GET'])
def home():
    return jsonify(message=f"Hello from Server: {server_id}", status="successful"), 200

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return '', 200  

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)