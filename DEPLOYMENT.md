# Deployment Guide

Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/davegornshtein/parakeet-tdt-deployment.git
cd parakeet-tdt-deployment
```

### 2. Download Models

Models are not included in the repository due to size. Download them separately:

```bash
# Create models directory
mkdir -p models

# Download Parakeet ASR
python src/scripts/download_model.py --model parakeet-tdt-0.6b-v2

# Download other models as needed
python src/scripts/download_model.py --model gemma-3-12b-it
python src/scripts/download_model.py --model phi-4-multimodal
```

### 3. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Required environment variables:
- PostgreSQL credentials
- Redis password
- MinIO credentials
- API keys (Tavily, Brave Search)

### 4. Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 5. Initialize Database

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python src/scripts/initialize_database.py
```

### 6. Start Backend

```bash
# Start the API server
python src/api/music_analyzer_api.py

# API will be available at http://localhost:8000
```

### 7. Start Frontend

```bash
# Install frontend dependencies
cd music-analyzer-frontend
npm install

# Start development server
npm start

# Frontend will be available at http://localhost:3000
```

## Production Deployment

### Using Docker

```bash
# Build production image
docker build -t music-analyzer:latest .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Using Systemd

Create service file at `/etc/systemd/system/music-analyzer.service`:

```ini
[Unit]
Description=Music Analyzer API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/music-analyzer
Environment="PATH=/opt/music-analyzer/venv/bin"
ExecStart=/opt/music-analyzer/venv/bin/python src/api/music_analyzer_api.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable music-analyzer
sudo systemctl start music-analyzer
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name music-analyzer.example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring

### Health Checks

- API Health: `http://localhost:8000/api/v2/health`
- Frontend Health: `http://localhost:3000/health`

### Logs

- API logs: `docker-compose logs -f api`
- PostgreSQL logs: `docker-compose logs -f postgres`
- Redis logs: `docker-compose logs -f redis`

### Metrics

Consider adding:
- Prometheus for metrics collection
- Grafana for visualization
- ELK stack for log aggregation

## Backup

### Database Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U music_user music_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U music_user music_db < backup.sql
```

### MinIO Backup

```bash
# Sync to backup location
mc mirror minio/music-files /backup/minio/
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify credentials in .env
   - Check pgvector extension is installed

2. **Model Loading Failed**
   - Ensure models are downloaded
   - Check GPU memory availability
   - Verify CUDA installation

3. **Frontend Build Failed**
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall

### Debug Mode

```bash
# Run API in debug mode
DEBUG=1 python src/api/music_analyzer_api.py

# Enable verbose logging
export LOG_LEVEL=DEBUG
```

## Support

For deployment assistance:
- Email: david@eveara.com
- Documentation: [README.md](README.md)
- Issues: [GitHub Issues](https://github.com/davegornshtein/parakeet-tdt-deployment/issues)