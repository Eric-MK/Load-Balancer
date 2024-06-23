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


