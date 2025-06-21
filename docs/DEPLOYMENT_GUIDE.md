# Music Analyzer Deployment Guide

## External HTTPS Access Configuration

Your Music Analyzer application is now fully deployed and accessible via HTTPS from anywhere on the internet.

### Access URLs

- **Main Application**: https://35.232.20.248/
- **Health Check**: https://35.232.20.248/health
- **API Documentation**: https://35.232.20.248/api/docs

### Protected Endpoints

#### Service Monitoring Dashboard
- URL: https://35.232.20.248/monitor/dashboard.html
- Username: `monitor`
- Password: `Monitor2025!`

#### MinIO Console (Object Storage)
- URL: https://35.232.20.248/minio-console/
- Username: `admin`
- Password: `MusicAnalyzer2025!`
- MinIO Root User: `minio_admin`
- MinIO Root Password: `minio_secret_2025`

#### MinIO S3 API
- URL: https://35.232.20.248/minio-api/
- Basic Auth: Same as MinIO Console
- Use for S3-compatible operations

### API Authentication

Protected API endpoints require Basic Authentication:
- Username: `parakeet`
- Password: `Q7+vD#8kN$2pL@9`

Example:
```bash
curl -k -u parakeet:Q7+vD#8kN$2pL@9 https://35.232.20.248/api/v2/health
```

### SSL Certificate

Currently using a self-signed certificate. Browsers will show a security warning that you need to accept.

To use with curl, add the `-k` flag to bypass certificate verification.

### Services Architecture

```
Internet
    |
    v
NGINX (HTTPS:443)
    |
    +-- Music Analyzer Frontend (React)
    |
    +-- Music Analyzer API (FastAPI:8000)
    |       |
    |       +-- PostgreSQL (5432)
    |       +-- Redis (6379)
    |       +-- MinIO (9000)
    |
    +-- MinIO Console (9001)
    |
    +-- Service Monitor Dashboard
```

### Service Management

All services are managed by systemd and will automatically start on boot:

```bash
# Check all services status
sudo systemctl status postgresql redis-server minio music-analyzer service-monitor

# Restart a service
sudo systemctl restart music-analyzer

# View logs
sudo journalctl -u music-analyzer -f
```

### Monitoring

The Service Monitor runs continuously and:
- Checks all services every 60 seconds
- Monitors disk space (alerts at 80% warning, 90% critical)
- Logs alerts to system journal and `/home/davegornshtein/parakeet-tdt-deployment/logs/alerts.log`
- Updates status in `/home/davegornshtein/parakeet-tdt-deployment/logs/current_status.json`

### Security Features

1. **NGINX Security Headers**: HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
2. **Rate Limiting**: 
   - API endpoints: 10 requests/second
   - Upload endpoint: 2 requests/second
3. **Basic Authentication** on sensitive endpoints
4. **CORS** configured for the external IP
5. **GCloud Firewall** allows only HTTP/HTTPS traffic

### Troubleshooting

1. **502 Bad Gateway**: Check if Music Analyzer service is running
   ```bash
   sudo systemctl status music-analyzer
   ```

2. **SSL Certificate Issues**: The self-signed certificate may cause warnings. For production, consider using Let's Encrypt with a domain name.

3. **Service Down**: Check the service monitor dashboard or run:
   ```bash
   /home/davegornshtein/parakeet-tdt-deployment/scripts/check_status.sh
   ```

### Backup Recommendations

1. **Database**: Set up regular PostgreSQL backups
2. **MinIO Data**: Located at `/home/davegornshtein/minio-data`
3. **Application Data**: Located at `/home/davegornshtein/parakeet-tdt-deployment/music_library_v2`

### Performance Tuning

Current configuration supports:
- 100MB max file upload size
- 600-second timeouts for long operations
- Connection pooling for all services
- HTTP/2 enabled for better performance

### Future Improvements

1. **Domain Name**: Register a domain and use Let's Encrypt for proper SSL
2. **CDN**: Consider CloudFlare for better global performance
3. **Backup Strategy**: Implement automated backups to GCS
4. **Monitoring**: Add Prometheus/Grafana for detailed metrics
5. **Load Balancing**: Scale horizontally with multiple instances