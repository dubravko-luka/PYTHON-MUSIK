#!/bin/bash

# List files in the directory
ls -la

# Remove unused Docker images
docker image prune -f

# Remove old Docker image if it exists
OLD_IMAGE_ID=$(docker images -q musik)
if [ ! -z "$OLD_IMAGE_ID" ]; then
    echo "Removing old Docker image: $OLD_IMAGE_ID"
    docker rmi -f $OLD_IMAGE_ID
fi

# Pull the latest code from the Git repository
git pull origin main

# Build the Docker image
docker build -t musik .

# Remove the old container if it exists
docker rm -f musik || true

# Run the Docker container
docker run -d -p 5000:5000 --name musik musik