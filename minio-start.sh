#!/bin/bash
# MinIO startup script

# Create data directory
mkdir -p /home/davegornshtein/minio-data

# Set environment variables
export MINIO_ROOT_USER=minio_admin
export MINIO_ROOT_PASSWORD=minio_secret_2025

# Start MinIO server
/home/davegornshtein/minio server /home/davegornshtein/minio-data --console-address :9001