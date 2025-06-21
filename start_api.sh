#!/bin/bash
# Startup script for Parakeet API with proper environment setup

# Set up environment
export PATH="/home/davegornshtein/parakeet-env/bin:$PATH"
export PYTHONPATH="/home/davegornshtein/parakeet-tdt-deployment:$PYTHONPATH"

# Activate virtual environment
source /home/davegornshtein/parakeet-env/bin/activate

# Change to working directory
cd /home/davegornshtein/parakeet-tdt-deployment

# Start the API server
exec python parakeet_api_complete.py