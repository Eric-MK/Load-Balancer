from flask import Flask, request, jsonify
from docker.errors import APIError, ContainerError
import json
import random
import requests
import docker
import re



app = Flask(__name__)

client = docker.from_env()

# Initialize global list
server_containers = []

def update_server_containers():
    global server_containers
    containers = client.containers.list()
    server_containers = [container.name for container in containers if 'server' in container.name.lower()]

@app.route('/rep', methods=['GET'])
def get_replicas():
    # Optionally update the list on every request
    update_server_containers()
    
    return jsonify({
        "message": {
            "N": len(server_containers),
            "replicas": server_containers
        },
        "status": "successful"
    }), 200

# add
@app.route('/add', methods=['POST'])
def add_servers():
    data = request.json
    if not data or 'n' not in data:
        return jsonify({"message": "Invalid request payload: Length of hostname list must match the number of new instances", "status": "failure"}), 400

    num_servers = data['n']
    hostnames = data.get('hostnames')

    if hostnames and len(hostnames) != num_servers:
        return jsonify({"message": "Length of hostname list must match the number of new instances", "status": "failure"}), 400

    if not hostnames:
        # List all current containers
        containers = client.containers.list()

        # Function to extract numbers from container names
        def extract_number(name):
            match = re.search(r'\d+', name)
            return int(match.group()) if match else None

        # Find the highest number used in container names
        max_number = max((extract_number(container.name) for container in containers), default=0)

        hostnames = [f"server_{max_number + i + 1}" for i in range(num_servers)]
   
    for hostname in hostnames:
        try:
            container = client.containers.run("myproject_server", 
                                              name=hostname,
                                              ports={'5000/tcp': None},
                                              detach=True,
                                              environment=[f"SERVER_ID={hostname}"])
            server_containers.append(container.name)
        except (APIError, ContainerError) as e:
            return jsonify({"message": f"Failed to create container {hostname}: {str(e)}", "status": "failure"}), 500
    update_server_containers()  # Update the global list
    return jsonify({
        "message": {
            "N": len(server_containers),
            "replicas": server_containers
        },
        "status": "successful"
    }), 200
    
if __name__ == '__main__':
        update_server_containers()  # Initial update at startup
        app.run(host='0.0.0.0', port=5000, debug=True)