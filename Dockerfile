# Dockerfile - Generic Python service base for the Godfather Bot
FROM python:3.11-bullseye

# Set the working directory in the container
WORKDIR /app

# Install essential system dependencies
# build-essential and swig are needed for some Python packages
RUN apt-get update && \
    apt-get install -y build-essential swig && \
    pip install --upgrade pip && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# The CMD is removed from here and will be specified in docker-compose.yml for each service