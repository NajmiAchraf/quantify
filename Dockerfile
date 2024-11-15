# Use the official Ubuntu 22.04 image from the Docker Hub
FROM ubuntu:22.04

# Install Python 3.7 and the required packages
RUN apt-get update -y
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt-get update -y
RUN apt-get install -y python3.7
RUN apt-get install -y python3.7-dev
RUN apt-get install -y python3-pip
RUN apt-get install -y gcc
RUN apt-get install -y clang
RUN apt-get install -y git
RUN apt-get install -y cmake
RUN apt-get install -y make
RUN apt-get install -y build-essential
RUN apt-get install -y libssl-dev
RUN apt-get install -y libffi-dev
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies of Python 3.7
RUN python3.7 -m pip install --upgrade pip
RUN python3.7 -m pip install -r requirements.txt