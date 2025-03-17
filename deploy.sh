#!/bin/bash

# List files in the directory
ls -la

# Remove unused Docker images
docker image prune -f

# Pull the latest code from the Git repository
git pull origin main

# Build the Docker image
docker build -t musik .

# Check if the container is already running
if [ "$(docker ps -q -f name=musik)" ]; then
    # If it is running, stop and remove the existing container
    docker stop musik
    docker rm musik
fi

# Run the Docker container
docker run -d -p 5000:5000 --name musik musik