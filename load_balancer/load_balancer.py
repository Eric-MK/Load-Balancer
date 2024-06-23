from flask import Flask, request, jsonify
from docker.errors import APIError, ContainerError
import json
import random
import docker
import re
import logging
import requests
import os

app = Flask(__name__)

client = docker.from_env()

# Initialize global list
server_containers = []

def update_server_containers():
    global server_containers
    containers = client.containers.list()
    server_containers = [container.name for container in containers if 'server' in container.name.lower()]
    # Update consistent hash with current servers
    consistent_hash.hash_ring.clear()
    consistent_hash.server_map.clear()
    for server in server_containers:
        consistent_hash.add_server(server)

def spawn_server(hostname):
    try:
        container = client.containers.run(
            "myproject_server", 
            name=hostname,
            ports={'5000/tcp': None},
            detach=True,
            environment=[f"SERVER_ID={hostname}"],
            network="loadbalancing_default"  # Specify the network
        )
        server_containers.append(container.name)
        consistent_hash.add_server(container.name)  # Add to consistent hash
    except (APIError, ContainerError) as e:
        logging.error(f"Failed to create container {hostname}: {str(e)}")

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

# Add servers
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
        spawn_server(hostname)
        
    update_server_containers()  # Update the global list
    return jsonify({
        "message": {
            "N": len(server_containers),
            "replicas": server_containers
        },
        "status": "successful"
    }), 200

# Remove servers
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

    # Stop and remove the selected hostnames
    for hostname in hostnames_to_remove:
        try:
            logging.info(f"Attempting to stop and remove container: {hostname}")
            container = client.containers.get(hostname)
            container.stop()
            container.remove()
            logging.info(f"Successfully stopped and removed container: {hostname}")
            server_containers.remove(hostname)
            consistent_hash.remove_server(hostname)  # Remove from consistent hash
        except (APIError, ContainerError) as e:
            logging.error(f"Failed to remove container {hostname}: {str(e)}")
            return jsonify({"message": f"Failed to remove container {hostname}: {str(e)}", "status": "failure"}), 500

    # Update the list of running containers
    update_server_containers()
    logging.info(f"Updated server containers list: {server_containers}")

    return jsonify({
        "message": {
            "N": len(server_containers),
            "replicas": server_containers
        },
        "status": "successful"
    }), 200


@app.route('/spawn', methods=['POST'])
def spawn_container():
    data = request.json
    image = data.get('image')
    name = data.get('name')
    network = data.get('network', 'net1')
    env_vars = data.get('env', {})

    env_options = ' '.join([f"-e {key}={value}" for key, value in env_vars.items()])
    command = f'sudo docker run --name {name} --network {network} --network-alias {name} {env_options} -d {image}'
    
    result = os.popen(command).read()
    if len(result) == 0:
        return jsonify({"message": "Unable to start container", "status": "failure"}), 500
    else:
        return jsonify({"message": "Successfully started container", "status": "success"}), 200

@app.route('/remove', methods=['POST'])
def remove_container():
    data = request.json
    name = data.get('name')

    stop_command = f'sudo docker stop {name}'
    remove_command = f'sudo docker rm {name}'

    stop_result = os.system(stop_command)
    remove_result = os.system(remove_command)

    if stop_result == 0 and remove_result == 0:
        return jsonify({"message": "Successfully removed container", "status": "success"}), 200
    else:
        return jsonify({"message": "Unable to remove container", "status": "failure"}), 500

import hashlib
import bisect

class ConsistentHash:
    def __init__(self, num_slots=512, virtual_servers_per_server=9):
        self.num_slots = num_slots
        self.virtual_servers_per_server = virtual_servers_per_server
        self.hash_ring = []
        self.server_map = {}

    # sh256
    def _hash_function(self, key):
    """Basic hash function"""
    if isinstance(key, int):
        key = str(key)  # Convert integer key to string
    return int(hashlib.sha256(key.encode('utf-8')).hexdigest(), 16) % self.num_slots

    # md5
    ''' def _hash_function(self, key):
        if isinstance(key, int):
            key = str(key)  # Convert integer key to string
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16) % self.num_slots '''

    def _virtual_server_hash(self, server_id, replica_id):
        combined_id = f"{server_id}#{replica_id}"
        hash_value = self._hash_function(combined_id)
        return hash_value

    
    def add_server(self, server_id):
        """Add server and its replicas to the hash ring"""
        for i in range(self.virtual_servers_per_server):
            virtual_hash = self._virtual_server_hash(server_id, i)
            self.hash_ring.append(virtual_hash)
            self.server_map[virtual_hash] = server_id
        self.hash_ring.sort()
    
    def remove_server(self, server_id):
        """Remove server and its replicas from the hash ring"""
        self.hash_ring = [h for h in self.hash_ring if self.server_map[h] != server_id]
        self.server_map = {h: s for h, s in self.server_map.items() if s != server_id}
    
    def get_server(self, key):
        """Get server for the given key"""
        if not self.hash_ring:
            return None
        hash_value = self._hash_function(key)
        idx = bisect.bisect(self.hash_ring, hash_value)
        if idx == len(self.hash_ring):
            idx = 0
        return self.server_map[self.hash_ring[idx]]

# Initialize the consistent hash
consistent_hash = ConsistentHash()

@app.route('/<path>', methods=['GET'])
def route_request(path):
    update_server_containers()  # Ensure server list is updated
    # Assume unique request ID is passed as a query parameter, e.g., /home?request_id=12345
    request_id = request.args.get('request_id', path)  # Default to path if no request_id provided
    target_server = consistent_hash.get_server(request_id)
    
    if target_server:
        try:
            response = requests.get(f"http://{target_server}:5000/{path}")
            return jsonify({"message": response.text, "server": target_server}), response.status_code
        except requests.exceptions.RequestException as e:
            # Detect failure and spawn new server instance
            logging.error(f"Error forwarding request to {target_server}: {str(e)}. Spawning a new instance.")
            new_hostname = "server_{}".format(max([int(re.search(r'\d+', name).group()) for name in server_containers]) + 1)
            spawn_server(new_hostname)
            return jsonify({"message": f"Error forwarding request to {target_server}: {str(e)}. New server instance {new_hostname} spawned.", "status": "failure"}), 500
    else:
        return jsonify({"message": "No available servers to handle the request", "status": "failure"}), 500

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    update_server_containers()  # Initial update at startup
    app.run(host='0.0.0.0', port=5000, debug=True)
