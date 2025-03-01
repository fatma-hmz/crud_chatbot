#!/bin/bash

# Update package list
sudo apt update

# Install PostgreSQL client
sudo apt install -y postgresql-client postgresql-client-common

# Add audio device
sudo apt install pulseaudio


# Install Python dependencies
pip install -r requirements.txt
