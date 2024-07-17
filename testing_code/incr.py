# Increment N testing from 2 to 6 

import asyncio
import aiohttp
import random
import time
import requests
import matplotlib.pyplot as plt

# Function to generate a random 6-digit request ID
def generate_request_id():
    return str(random.randint(100000, 999999))

async def send_request(session, url):
    async with session.get(url) as response:
        return await response.json()

async def main(url, num_requests):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(num_requests):
            request_id = generate_request_id()  # Generate random 6-digit request ID
            request_url = f"{url}?request_id={request_id}"  # Include request ID in URL
            tasks.append(send_request(session, request_url))
        responses = await asyncio.gather(*tasks)
        return responses

url = 'http://localhost:5000/home'  
num_requests = 10000

server_counts = []
average_loads = []

for N in range(2, 7):
    # Add servers
    add_response = requests.post("http://localhost:5000/add", json={"n": 1})
    if add_response.status_code != 200:
        print(f"Failed to add servers: {add_response.json()}")
        continue

    # Allow some time for the server to start
    time.sleep(5)

    # Send requests
    responses = asyncio.run(main(url, num_requests))

    # Count requests handled by each server
    counts = {}
    for response in responses:
        server = response.get('server', 'error')
        if server in counts:
            counts[server] += 1
        else:
            counts[server] = 1

    # Calculate the average load per server
    avg_load = sum(counts.values()) / len(counts)
    average_loads.append(avg_load)

    # Print the counts for debugging
    print(f"Server counts for N={N}: {counts}")

# Plot the results
plt.plot(range(2, 7), average_loads, marker='o')
plt.xlabel('Number of Servers')
plt.ylabel('Average Load per Server')
plt.title('Average Load per Server vs Number of Servers')
plt.show()
