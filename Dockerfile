# The official Ubuntu 22.04 image from the Docker Hub
FROM ubuntu:22.04

RUN apt-get update -y

# Install Python 3
RUN apt-get update -y
RUN apt-get install -y python3-dev python3-venv python3-pip

# Install C/C++ compilers
RUN apt-get install -y clang

# Install CMake and Make
RUN apt-get install -y cmake make

# Install OpenMPI
RUN apt-get install -y openmpi-bin libopenmpi-dev

# Install Git
RUN apt-get install -y git

# Install other dependencies
RUN apt-get install -y build-essential libssl-dev libffi-dev

# Clean up
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies of Python 3
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt
RUN python3 -m pip install mpi4py

# Copy the Python script into the container
COPY insert_missed_code.py .

# Run the Python script
RUN python3 insert_missed_code.py docker