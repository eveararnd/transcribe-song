# Music Analyzer V2 - Complete System Documentation

## Overview

Music Analyzer V2 is a comprehensive music analysis system that provides:
- Audio file upload and management
- Automatic speech recognition (ASR) for music transcription
- Lyrics search from multiple sources
- Semantic search capabilities
- Export functionality in multiple formats
- Web-based user interface

## System Architecture

### Backend Components
1. **FastAPI Application** (`music_analyzer_api.py`)
   - RESTful API endpoints
   - File upload and management
   - Integration with ASR models
   - Search functionality

2. **Database** (PostgreSQL with pgvector)
   - Music file metadata storage
   - Transcriptions and lyrics
   - Vector embeddings for semantic search

3. **Storage**
   - **MinIO**: Object storage for audio files
   - **Local filesystem**: Backup storage
   - **Redis**: Caching layer

4. **ML Models**
   - **Parakeet ASR**: Audio transcription
   - **Sentence Transformers**: Text embeddings
   - **FAISS**: Vector similarity search

### Frontend Components
- **React/TypeScript** application
- **Material-UI** for component library
- **React Query** for data fetching
- **Axios** for API communication

## API Endpoints

### Authentication
All endpoints require HTTP Basic Authentication.

### Core Endpoints

#### File Management
- `POST /api/v2/upload` - Upload music file
- `GET /api/v2/files` - List all files
- `GET /api/v2/files/{file_id}` - Get file details
- `DELETE /api/v2/files/{file_id}` - Delete file

#### Transcription
- `POST /api/v2/transcribe` - Transcribe audio file
- `GET /api/v2/files/{file_id}/transcriptions` - Get transcriptions

#### Lyrics
- `POST /api/v2/search-lyrics` - Search for lyrics
- `GET /api/v2/files/{file_id}/lyrics` - Get saved lyrics

#### Search
- `POST /api/v2/search/similar` - Find similar content
- `POST /api/v2/search/lyrics` - Search by lyrics

#### Export
- `GET /api/v2/export/{file_id}` - Export single file
- `POST /api/v2/export/batch` - Batch export

Supported formats:
- `json` - Complete data in JSON
- `csv` - Spreadsheet format
- `xlsx` - Excel workbook
- `zip` - Complete export with audio
- `tar.gz` - Original audio files
- `mono_tar.gz` - Mono files with metadata

#### Storage
- `GET /api/v2/storage/stats` - Storage statistics
- `POST /api/v2/storage/cleanup` - Cleanup old files

## Frontend Features

### Pages
1. **Dashboard** (`/`)
   - Overview of uploaded files
   - Storage statistics
   - Quick actions

2. **Upload** (`/upload`)
   - Drag-and-drop interface
   - Multiple file upload
   - Progress tracking

3. **File Details** (`/file/:id`)
   - Complete file information
   - Transcriptions tab
   - Lyrics tab
   - Export options

4. **Search** (`/search`)
   - Similar content search
   - Lyrics search
   - Result previews

## Deployment

### Backend Deployment

1. **Environment Setup**
```bash
# Create .env file with required variables
cp .env.example .env
# Edit .env with your credentials
```

2. **Database Setup**
```bash
# PostgreSQL with pgvector
docker-compose up -d postgres
```

3. **Storage Services**
```bash
# MinIO and Redis
docker-compose up -d minio redis
```

4. **Run API**
```bash
python3 music_analyzer_api.py
```

### Frontend Deployment

1. **Development**
```bash
cd music-analyzer-frontend
npm install
npm start
```

2. **Production**
```bash
# Build frontend
npm run build

# Deploy with nginx
sudo ./deploy-frontend.sh
```

## Configuration Files

### Docker Compose (`docker-compose.yml`)
- PostgreSQL with pgvector
- Redis
- MinIO

### Nginx Configuration
- `nginx.conf` - Backend API proxy
- `nginx-frontend.conf` - Frontend serving

### Environment Variables
```env
# Database
POSTGRES_USER=parakeet
POSTGRES_PASSWORD=parakeetdb123
POSTGRES_DB=music_analyzer

# Redis
REDIS_PASSWORD=redis123

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minio123456

# API Keys
TAVILY_API_KEY=your_key
BRAVE_SEARCH_API_KEY=your_key

# Model paths
PARAKEET_MODEL_PATH=/path/to/model
```

## Usage Examples

### Upload and Transcribe
```bash
# Upload file
curl -u user:pass -X POST \
  -F "file=@song.mp3" \
  http://localhost:8000/api/v2/upload

# Transcribe
curl -u user:pass -X POST \
  -H "Content-Type: application/json" \
  -d '{"file_id": "file-id-here"}' \
  http://localhost:8000/api/v2/transcribe
```

### Export Examples
```bash
# Export as tar.gz
curl -u user:pass \
  "http://localhost:8000/api/v2/export/file-id?format=tar.gz" \
  -o export.tar.gz

# Batch export mono files
curl -u user:pass -X POST \
  -H "Content-Type: application/json" \
  -d '{"file_ids": ["id1", "id2"], "format": "mono_tar.gz"}' \
  http://localhost:8000/api/v2/export/batch \
  -o batch.tar.gz
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check username/password
   - Verify nginx is passing auth headers

2. **Upload Failed**
   - Check file format is supported
   - Verify storage permissions
   - Check MinIO is running

3. **Transcription Timeout**
   - Large files may take time
   - Check ASR model is loaded
   - Verify GPU/CPU resources

4. **Search No Results**
   - Ensure files are transcribed
   - Check FAISS index exists
   - Verify embeddings are generated

## System Requirements

### Backend
- Python 3.8+
- PostgreSQL 13+ with pgvector
- Redis 6+
- MinIO (latest)
- 8GB+ RAM recommended
- GPU recommended for ASR

### Frontend
- Node.js 16+
- Modern web browser

## Security Considerations

1. **Authentication**: HTTP Basic Auth (use HTTPS in production)
2. **File Validation**: Type and size checks
3. **Input Sanitization**: All user inputs sanitized
4. **CORS**: Configured for frontend origin
5. **Rate Limiting**: Consider adding for production

## Future Enhancements

1. **Multi-user Support**: User accounts and permissions
2. **Batch Processing**: Queue system for large uploads
3. **Advanced Search**: More search options and filters
4. **API Rate Limiting**: Protect against abuse
5. **Monitoring**: Add logging and metrics
6. **Backup System**: Automated backups