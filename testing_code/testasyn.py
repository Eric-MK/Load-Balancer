# Testing async requests to the load balancer

import asyncio
import aiohttp
import random

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

# Function to generate a random 6-digit request ID
def generate_request_id():
    return str(random.randint(100000, 999999))

url = 'http://localhost:5000/home'  
num_requests = 10000

responses = asyncio.run(main(url, num_requests))

# Count requests handled by each server
server_counts = {}
for response in responses:
    server = response['server']
    if server in server_counts:
        server_counts[server] += 1
    else:
        server_counts[server] = 1

# Print the counts
for server, count in server_counts.items():
    print(f'{server}: {count}')

# Generate bar chart
import matplotlib.pyplot as plt

servers = list(server_counts.keys())
counts = list(server_counts.values())

plt.bar(servers, counts)
plt.xlabel('Server')
plt.ylabel('Request Count')
plt.title('Requests Handled by Each Server (N=3)')
plt.show()
