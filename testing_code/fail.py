# Test for Server Failure and how it response

import requests
import time
import json
import random

BASE_URL = 'http://localhost:5000'

def generate_request_id():
    return str(random.randint(100000, 999999))

def add_servers(n):
    response = requests.post(f'{BASE_URL}/add', json={'n': n})
    print('Add Servers:', response.json())

def remove_servers(n):
    response = requests.delete(f'{BASE_URL}/rm', json={'n': n})
    print('Remove Servers:', response.json())

def send_request(path):
    request_id = generate_request_id()
    response = requests.get(f'{BASE_URL}/home?request_id={request_id}')
    print(f'Request: {path}, Request ID: {request_id}, Response: {response.json()}')

def failure_handling_test():
    print("Starting Failure Handling Test")
    add_servers(4)
    time.sleep(2)  # Wait for servers to start

    print("Sending initial requests")
    for i in range(10):
        send_request(f'home')

    print("Removing some servers")
    remove_servers(2)
    time.sleep(2)  # Wait for servers to be removed

    print("Sending requests after removing servers")
    for i in range(10, 20):
        send_request(f'home')

def scaling_down_test():
    print("Starting Scaling Down Test")
    add_servers(6)
    time.sleep(2)  # Wait for servers to start

    print("Sending initial requests")
    for i in range(10):
        send_request(f'home')

    print("Scaling down by removing servers")
    remove_servers(4)
    time.sleep(2)  # Wait for servers to be removed

    print("Sending requests after scaling down")
    for i in range(10, 20):
        send_request(f'home')

if __name__ == "__main__":
    failure_handling_test()
    scaling_down_test()
