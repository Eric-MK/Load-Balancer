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