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

#add
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
    
#remove
@app.route('/rm', methods=['DELETE'])
def remove_servers():
    data = request.get_json()
    if not data or 'n' not in data or (data.get('hostnames') and len(data['hostnames']) > data['n']):
        return jsonify({"message": "<Error> Invalid request payload", "status": "failure"}), 400

    num_to_remove = data['n']
    hostnames_to_remove = data.get('hostnames')

    if hostnames_to_remove:
        # Check if all specified hostnames exist
        if not all(hostname in server_containers for hostname in hostnames_to_remove):
            return jsonify({
                "message": "<Error> One or more specified hostnames do not exist",
                "status": "failure"
            }), 400
        if len(hostnames_to_remove) != num_to_remove:
            return jsonify({
                "message": "<Error> Length of hostname list must match the number of instances to be removed",
                "status": "failure"
            }), 400
    else:
        # If no hostnames provided, select random hostnames to remove
        if num_to_remove > len(server_containers):
            return jsonify({"message": "<Error> Trying to remove more instances than available", "status": "failure"}), 400
        hostnames_to_remove = random.sample(server_containers, num_to_remove)

    # Remove the selected hostnames
    for hostname in hostnames_to_remove:
        server_containers.remove(hostname)

    return jsonify({
        "message": {
            "N": len(server_containers),
            "replicas": server_containers
        },
        "status": "successful"
    }), 200



"""

#define the hash functions
def request_hash(i):
    return (i + 2 * i**2 + 17) % 512

def virtual_server_hash(i, j):
    return (i + j + 2 * j**2 + 25) % 512


#create the consistent hash map
def initialize_hash_map(n, k, slots):
    hash_map = [None] * slots
    for i in range(n):
        for j in range(k):
            slot = virtual_server_hash(i, j)
            # Implementing linear probing to resolve collisions
            while hash_map[slot] is not None:
                slot = (slot + 1) % slots #assign server container ID to the slot
            hash_map[slot] = i
    return hash_map


#Map requaests to the hash map
def map_request_to_server(request_id, hash_map):
    slot = request_hash(request_id)
    server_id = hash_map[slot]
    if server_id is None:
        #Implement linear probing for unassigned slots
        original_slot = slot
        while hash_map[slot] is None:
            slot = (slot + 1) % 512
            if slot == original_slot:
                raise Exception("No available server found, hash map is full")
    return hash_map[slot]

# Initialize the hash map parameters
N = 3  # Number of servers
K = 9  # Number of replicas per server
SLOTS = 512  # Total slots in the hash ring
consistent_hash_map = initialize_hash_map(N, K, SLOTS)
servers = ["http://localhost:5001", "http://localhost:5002", "http://localhost:5003"]  # Base URLs of the server containers



 @app.route('/<path:path>',methods=['GET'])
def proxy_request(path):
    try:
        # Convert incoming path to a unique integer hash code, you might need to adjust logic based on actual path usage
        request_id = hash(path)
        # Map this request ID to a server using your consistent hash map
        server_index = map_request_to_server(request_id, consistent_hash_map)
        target_server = servers[server_index]
        # Forward the request to the correct server and retrieve the response
        response = requests.get(f"{target_server}/{path}")
        if response.status_code == 404:
            return jsonify({"message": f"Error: '/{path}' endpoint does not exist in server replicas", "status": "failure"}), 400
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"message": str(e), "status": "failure"}), 500
"""


if __name__ == '__main__':
        update_server_containers()  # Initial update at startup
        app.run(host='0.0.0.0', port=5000, debug=True)