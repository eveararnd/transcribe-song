#!/bin/bash

# Music Analyzer Frontend Deployment Script

set -e

echo "Music Analyzer Frontend Deployment"
echo "=================================="

# Check if running as root for nginx operations
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root for nginx configuration"
    exit 1
fi

# Variables
FRONTEND_DIR="/home/davegornshtein/parakeet-tdt-deployment/music-analyzer-frontend"
BUILD_DIR="$FRONTEND_DIR/build"
DEPLOY_DIR="/var/www/music-analyzer"
NGINX_CONF="/etc/nginx/sites-available/music-analyzer"
NGINX_ENABLED="/etc/nginx/sites-enabled/music-analyzer"

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Error: Frontend directory not found at $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build the frontend
echo "Building frontend..."
npm run build

# Create deployment directory
echo "Creating deployment directory..."
mkdir -p "$DEPLOY_DIR"

# Copy build files
echo "Deploying build files..."
cp -r "$BUILD_DIR"/* "$DEPLOY_DIR/"

# Set proper permissions
chown -R www-data:www-data "$DEPLOY_DIR"
chmod -R 755 "$DEPLOY_DIR"

# Copy nginx configuration
echo "Configuring nginx..."
cp /home/davegornshtein/parakeet-tdt-deployment/nginx-frontend.conf "$NGINX_CONF"

# Enable the site
ln -sf "$NGINX_CONF" "$NGINX_ENABLED"

# Test nginx configuration
echo "Testing nginx configuration..."
nginx -t

# Reload nginx
echo "Reloading nginx..."
systemctl reload nginx

echo ""
echo "Deployment complete!"
echo "==================="
echo "Frontend deployed to: $DEPLOY_DIR"
echo "Nginx config: $NGINX_CONF"
echo ""
echo "The Music Analyzer frontend should now be accessible at:"
echo "http://localhost/"
echo ""
echo "Make sure the backend API is running on port 8000"