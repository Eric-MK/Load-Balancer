# Load Balancer Project

## Design Choices

- **load_balancer/**: Contains the load balancer application files.
- **myserver/**: Contains server application files used by the load balancer.
- **docker-compose.yml**: Defines Docker services for load balancer and server instances.
- **Makefile**: Provides convenient commands for Docker operations.
- **Flask**: Chosen for its lightweight and easy-to-use framework for building the load balancer and server applications.
- **Consistent Hashing**: Implemented for server selection based on request characteristics, ensuring distribution of load to the servers.
- **Docker**: Utilized for containerization, ensuring consistent deployment environments across different machines. 
- The containers created and added are in the same network environment for efficient communication e.g dynamic addition and removal of containers.

## Assumptions

- **Single Load Balancer**: The setup assumes a single load balancer instance handling all incoming requests.
- **Request Testing Endpoint**: Assumes testing the load balancer with requests to `http://localhost:5000/home` using different request IDs to verify load balancing functionality.
- Used 10 request to test the server failure response, for better visual on the terminal.
- **Development Environment**: Designed for development and testing purposes.

## Usage

### Prerequisites

- Docker Engine installed on the host machine.

### Building and Running

1. **Build Docker Images:**
```bash
   make build 
```
2. **Start Services:**
```bash
   make build
```
3. **Access Load Balancer**
- To check server replicas
```bash
    curl -X GET http://localhost:5000/rep
```
- To check heartbeat for server e.g. server1
```bash
    curl -X GET http://localhost:5001/heartbeat
```
- To add server e.g 3 servers
```bash
    curl -X POST http://localhost:5000/add     -H "Content-Type: application/json"     -d '{"n": 3}'
```
- To remove server e.g 1 server
```bash
   curl -X DELETE http://localhost:5000/rm     -H "Content-Type: application/json"     -d '{"n": 1}'
```
## Testing and Performance Analysis

1. **/rep endpoint `http://localhost:5000/rep`** 

![alt text](screenshot/image-1.png)

2. **/heartbeat endpoint e.g for server at `http://localhost:5002/hearbeat` server_2**

![alt text](screenshot/image-3.png)

3. **/home endpoint e.g for server at  `http://localhost:5001/home` server_1**

![alt text](screenshot/image-4.png)

4. **/add endpoint**
- provide the n field and a list of hostnames e.g adding 4:
``` bash
    curl -X POST http://localhost:5000/add -H "Content-Type: application/json" -d '{
    "n": 4,
    "hostnames": ["server_4", "server_5", "server_6", "server_7"]
}'
```
![alt text](screenshot/image-5.png)

- If no provide hostnames, they are generated automatically based on the number n e.g adding 3 servers:

``` bash
    curl -X POST http://localhost:5000/add -H "Content-Type: application/json" -d '{
    "n": 3
}'
```
![alt text](screenshot/image-6.png)

- To simulate an *error* where the n field is missing in the JSON payload:

``` bash
    curl -X POST http://localhost:5000/add -H "Content-Type: application/json" -d '{
    "hostnames": ["server_20", "server_21", "server_30"]
}'
```
![alt text](screenshot/image-7.png)

- confirm the replicas in the server after adding processes

![alt text](screenshot/image-8.png)

5. **/rem endpoint**
- provide the n field and a list of hostnames to remove e.g. server_1 and server_2:
``` bash
    curl -X DELETE http://localhost:5000/rm -H "Content-Type: application/json" -d '{
    "n": 2,
    "hostnames": ["server_1", "server_2"]
}'
```
![alt text](screenshot/image-9.png)

- No hostnames, they should be selected randomly to be removed e.g 3:
``` bash
    curl -X DELETE http://localhost:5000/rm -H "Content-Type: application/json" -d '{
    "n": 3
}'
```
![alt text](screenshot/image-10.png)

- Simulate an *error* situation where the length of hostnames exceeds n:
``` bash
    curl -X DELETE http://localhost:5000/rm -H "Content-Type: application/json" -d '{
    "n": 2,
    "hostnames": ["server_5", "server_7", "server_8"]
}'

```
![alt text](screenshot/image-12.png)

- confirmation of replicas after removing processes

![alt text](screenshot/image-13.png)

### Testing Load balancing

**A-1 Load Distribution Among 3 Servers**
#### Observations

![alt text](screenshot/Figure_1.png)

#### Analysis
- The load distribution is uneven, with `server_1` handling the most requests and `server_3` handling the least.
- Possible reasons for this discrepancy could include the network latency, or environmental factors.

**A-2 Scalability with Incrementing Servers N from 2 to 6**
#### Observations

![alt text](screenshot/Figure_2.png)

#### Analysis
- The average load per server decreases as the number of servers increases.
- The load balancer scales efficiently with more servers.

**A-3 Load Balancer Recovery from Server Failure**

#### Observations

![alt text](screenshot/image-14.png)

![alt text](screenshot/image-15.png)

![alt text](screenshot/image-16.png)

![alt text](screenshot/image-17.png)

#### Initial Requests with addition of 4 Servers

- **server_4**: 1 request
- **server_6**: 3 requests
- **server_1**: 1 request
- **server_2**: 2 requests
- **server_5**: 1 request
- **server_7**: 2 requests

#### Post-Failure Requests with deletion of 2 Servers

- **server_1**: 2 requests
- **server_2**: 3 requests
- **server_7**: 4 requests
- **server_4**: 1 request

**Observations**:
- The load balancer quickly detected the removal of 2 servers and redistributed the load.
- The response times remained stable, indicating efficient handling of server failures.

### Scaling Down Test

#### Initial Requests with addition of 6 Servers

- **server_8**: 2 requests
- **server_4**: 1 request
- **server_10**: 2 requests
- **server_9**: 1 request
- **server_2**: 4 requests

#### Post-Scaling Requests with removing 2 Servers

- **server_10**: 2 requests
- **server_12**: 2 requests
- **server_11**: 2 requests
- **server_9**: 2 requests
- **server_2**: 3 requests

**Observations**:
- The load balancer effectively scaled down when deletion of 2 servers.
- The load distribution post-scaling was balanced, and the system maintained the performance.

### Testing Load balancing for A-4 modifing the hash and virtual server functions using md5

**A-1 Load Distribution Among 3 Servers**
#### Observations

![alt text](screenshot/Figure_4.png)

#### Analysis

- The MD5 hash function resulted in an imbalanced load distribution among the servers, with one server handling a significantly higher number of requests.
- The load distribution with the MD5 hash function is less balanced compared to the original SHA-256 based hash function.
- This imbalance indicates that the MD5 hash function might not be as effective in distributing requests evenly across servers.

**A-2 Scalability with Incrementing Servers N from 2 to 6**
#### Observations

![alt text](screenshot/Figure_11.png)

#### Analysis

- The average load per server decreases as the number of servers increases, indicating good scalability.
- Despite the imbalances observed in A-1, the system scales well with the MD5 hash function, distributing the load across an increasing number of servers.