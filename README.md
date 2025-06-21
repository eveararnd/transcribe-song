# Music Analyzer V2 - Parakeet TDT Deployment

Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.

A comprehensive music analysis system with multi-model support, audio transcription, lyrics search, and advanced export capabilities.

## Overview

Music Analyzer V2 is a full-stack application that provides:
- Audio file upload and management
- Automatic speech recognition (ASR) for music transcription
- Multi-language model support (Phi-4, Gemma)
- Lyrics search from multiple sources (Genius, Brave, Tavily)
- Semantic search using FAISS vector similarity
- Export functionality in multiple formats
- React/TypeScript web interface with model management UI

## Architecture

### System Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React Frontend│────▶│   FastAPI       │────▶│   PostgreSQL    │
│   (TypeScript)  │     │   Backend       │     │   + pgvector    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                          │
                              ▼                          ▼
                       ┌─────────────┐           ┌─────────────┐
                       │   MinIO     │           │    Redis    │
                       │  Storage    │           │   Cache     │
                       └─────────────┘           └─────────────┘
                              │
                              ▼
                       ┌─────────────────────────────────┐
                       │        ML Models                 │
                       ├─────────────────────────────────┤
                       │ • Parakeet ASR                  │
                       │ • Phi-4 (reasoning/multimodal)  │
                       │ • Gemma 3 12B                   │
                       │ • Sentence Transformers         │
                       └─────────────────────────────────┘
```

### Directory Structure

```
parakeet-tdt-deployment/
├── src/                          # Source code (organized structure)
│   ├── api/                      # API endpoints
│   │   ├── music_analyzer_api.py # Main FastAPI application
│   │   ├── parakeet_api.py       # Parakeet-specific endpoints
│   │   └── ...
│   ├── models/                   # Data models and ML managers
│   │   ├── music_analyzer_models.py  # Database models
│   │   ├── multi_model_manager.py    # Model orchestration
│   │   ├── gemma_manager.py          # Gemma model interface
│   │   └── ...
│   ├── managers/                 # Business logic managers
│   │   ├── faiss_manager.py      # FAISS vector search
│   │   ├── lyrics_search_manager.py  # Lyrics search
│   │   └── storage_manager.py    # File storage
│   ├── config/                   # Configuration
│   │   ├── music_analyzer_config.py  # App configuration
│   │   └── model_config_interface.py # Model configs
│   ├── utils/                    # Utilities
│   │   ├── music_analyzer_export.py  # Export functionality
│   │   └── ...
│   └── scripts/                  # Standalone scripts
│       ├── initialize_database.py
│       └── ...
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── component/                # Component tests
│   ├── system/                   # System integration tests
│   └── model/                    # Model-specific tests
├── music_library/                # Music files storage
├── music-analyzer-frontend/      # React frontend
├── docker-compose.yml            # Docker services
├── test_runner.py                # Unified test runner
└── requirements.txt              # Python dependencies
```

## Features

### 1. Audio File Management
- Upload music files in various formats (MP3, FLAC, WAV, etc.)
- Automatic metadata extraction (duration, sample rate, codec)
- Genre detection and categorization
- Duplicate detection using file hashing

### 2. Transcription & ASR
- Parakeet ASR for high-quality transcription
- Multi-language support
- Batch processing capabilities
- Caching for improved performance

### 3. Lyrics Search
- Multiple search providers:
  - Genius API for official lyrics
  - Brave Search for web results
  - Tavily API for AI-powered search
- Confidence scoring and result ranking
- Fallback mechanism between providers

### 4. Vector Search & Similarity
- FAISS-based semantic search
- Find similar songs by content
- Embedding generation using Sentence Transformers
- Efficient nearest neighbor search

### 5. Export Capabilities
- Multiple export formats:
  - JSON (structured data)
  - CSV (tabular format)
  - XLSX (Excel spreadsheet)
  - ZIP (bundled exports)
  - TAR.GZ (compressed archives)
- Batch export support
- Customizable export fields

### 6. Frontend Features
- Modern React/TypeScript interface
- Authentication system
- Real-time file upload progress
- Search and filter capabilities
- Responsive design
- Model management UI with load/unload controls

## Testing

### Test Structure

The project includes comprehensive testing across multiple levels:

- **Unit Tests** (`tests/unit/`): Test individual components
- **Component Tests** (`tests/component/`): Test integrated components
- **System Tests** (`tests/system/`): End-to-end testing
- **Model Tests** (`tests/model/`): ML model-specific tests
- **UI Tests**: React component testing with Vitest

### Running Tests

Use the unified test runner:

```bash
# Run all tests
python3 test_runner.py --all

# Run specific test suites
python3 test_runner.py --unit      # Unit tests only
python3 test_runner.py --system    # System tests only
python3 test_runner.py --ui        # UI tests only

# Additional options
python3 test_runner.py --unit --coverage  # With coverage report
python3 test_runner.py --all --verbose    # Verbose output
```

### Test Results

Current test status:
- UI Tests: 100% pass rate (87/87 tests)
- Python Tests: 96.4% pass rate (27/28 tests)
- Total Coverage: ~90%

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- CUDA-capable GPU (for model inference)
- PostgreSQL 14+ with pgvector extension

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/parakeet-tdt-deployment.git
cd parakeet-tdt-deployment
```

2. Create Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

3. Start Docker services:
```bash
docker-compose up -d
```

4. Initialize database:
```bash
python src/scripts/initialize_database.py
```

5. Install frontend dependencies:
```bash
cd music-analyzer-frontend
npm install
```

6. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Starting the Backend

```bash
python src/api/music_analyzer_api.py
# API will be available at http://localhost:8000
```

### Starting the Frontend

```bash
cd music-analyzer-frontend
npm start
# Frontend will be available at http://localhost:3000
```

### API Documentation

Once running, visit:
- Interactive API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

Key configuration options in `src/config/music_analyzer_config.py`:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for caching
- `MINIO_ENDPOINT`: MinIO object storage
- `MODEL_CACHE_DIR`: Directory for ML models
- `MAX_FILE_SIZE`: Maximum upload file size
- `SUPPORTED_FORMATS`: Allowed audio formats

## Development

### Code Style

- Python: Follow PEP 8, use Black formatter
- TypeScript: ESLint with Prettier
- Commit messages: Conventional Commits format

### Adding New Features

1. Create feature branch
2. Write tests first (TDD approach)
3. Implement feature
4. Ensure all tests pass
5. Update documentation
6. Submit pull request

## License

Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, modification, distribution, or use of this software, via any medium, is strictly prohibited.

## Support

For issues, questions, or contributions, please contact:
- Email: david@eveara.com
- GitHub Issues: [Project Issues](https://github.com/yourusername/parakeet-tdt-deployment/issues)

## Acknowledgments

- NVIDIA for Parakeet ASR model
- Microsoft for Phi-4 models
- Google for Gemma models
- Hugging Face for model hosting and tools