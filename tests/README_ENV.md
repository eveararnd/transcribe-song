# Test Environment Configuration

## Overview

All test files in this repository have been updated to use environment variables instead of hardcoded passwords. This improves security and makes it easier to manage different environments.

## Environment Variables

The test suite uses the following environment variables:

- `API_USERNAME`: Username for API authentication (default: "parakeet")
- `API_PASSWORD`: Password for API authentication  
- `TEST_API_URL`: Base URL for the API to test against
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: PostgreSQL database name
- `REDIS_PASSWORD`: Redis password
- `MINIO_ROOT_USER`: MinIO username
- `MINIO_ROOT_PASSWORD`: MinIO password
- `TAVILY_API_KEY`: Tavily API key for lyrics search
- `BRAVE_SEARCH_API_KEY`: Brave Search API key

## Configuration Files

1. **`.env`** - Main environment file with production/development credentials
2. **`.env.test`** - Test-specific environment file (loaded by test files)

## Usage

### Running Tests

Tests will automatically load environment variables from `.env.test`:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/system/test_music_analyzer_api.py

# Run with verbose output
python -m pytest -v tests/
```

### Setting Custom Environment Variables

You can override any environment variable for testing:

```bash
# Override API URL
TEST_API_URL=http://localhost:8001 python -m pytest tests/

# Override credentials
API_USERNAME=testuser API_PASSWORD=testpass python -m pytest tests/
```

### Different Environments

For different environments, create specific .env files:

- `.env.test` - Local testing
- `.env.staging` - Staging environment
- `.env.production` - Production environment

Then update the `load_dotenv()` call in test files to use the appropriate file.

## Security Notes

1. **Never commit `.env` files with real credentials to version control**
2. Add `.env*` to `.gitignore` to prevent accidental commits
3. Use different passwords for different environments
4. Rotate credentials regularly
5. Consider using a secrets management service for production

## Updated Test Files

The following test files have been updated to use environment variables:

- `tests/system/test_music_analyzer_api.py`
- `tests/unit/test_direct_transcribe.py`
- `tests/component/test_flac_transcription.py`
- `tests/component/test_flac_files.py`
- `tests/system/test_music_analyzer_integration.py`
- `tests/system/test_existing_catalog.py`
- `tests/component/test_v2_endpoints.py`
- `tests/component/test_local_api.py`
- `tests/component/music_transcription_test.py`

## Example .env.test File

```env
# API Authentication
API_USERNAME=parakeet
API_PASSWORD=your_secure_password_here

# Test API URLs
TEST_API_URL=https://35.232.20.248

# Database credentials
POSTGRES_USER=parakeet
POSTGRES_PASSWORD=parakeetdb123
POSTGRES_DB=music_analyzer

# Redis
REDIS_PASSWORD=redis123

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minio123456

# API Keys
TAVILY_API_KEY=your_tavily_api_key
BRAVE_SEARCH_API_KEY=your_brave_api_key
```

## Troubleshooting

1. **Missing environment variables**: If a test fails due to missing credentials, check that `.env.test` exists and contains all required variables.

2. **Wrong credentials**: Ensure the credentials in `.env.test` match what your API expects.

3. **Module not found**: Install `python-dotenv` if not already installed:
   ```bash
   pip install python-dotenv
   ```

4. **Different passwords for different APIs**: Some tests may use different passwords (e.g., nginx vs FastAPI). Make sure to set the correct password in the environment variable.