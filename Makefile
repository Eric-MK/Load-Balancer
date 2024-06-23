.PHONY: build up down logs restart prune ps docker-ps compose-ps network network-inspect container-logs

# Build the Docker containers without using cache
build:
	sudo docker-compose build --no-cache

# Start the Docker containers in detached mode
up:
	sudo docker-compose up -d

# Stop and remove the Docker containers
down:
	sudo docker-compose down

# Show logs of Docker containers
logs:
	sudo docker-compose logs

# Restart the Docker service
restart:
	sudo systemctl restart docker

# Remove all unused containers, networks, images (both dangling and unreferenced), and optionally, volumes
prune:
	sudo docker system prune -a -f

# List all running Docker containers
ps:
	sudo docker ps

# List containers managed by docker-compose
compose-ps:
	sudo docker-compose ps

# List all Docker networks
network:
	sudo docker network ls

# Inspect a specific Docker network
network-inspect:
	@echo "Usage: make network-inspect NETWORK=<network_name>"
	@[ -z "$(NETWORK)" ] && echo "Error: NETWORK variable is not set" && exit 1 || sudo docker network inspect $(NETWORK)

# Show logs of a specific container
container-logs:
	@echo "Usage: make container-logs CONTAINER=<container_name>"
	@[ -z "$(CONTAINER)" ] && echo "Error: CONTAINER variable is not set" && exit 1 || sudo docker logs $(CONTAINER)
