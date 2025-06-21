# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Model selector UI component with load/unload functionality
- Unified test runner script with command-line options
- Comprehensive documentation in README.md
- Copyright notices to all source files
- AUTHORS file with contributor information
- .gitattributes for proper file handling

### Changed
- **BREAKING**: Reorganized entire codebase from flat structure to `src/` directory hierarchy
  - API endpoints moved to `src/api/`
  - Model managers moved to `src/models/`
  - Business logic moved to `src/managers/`
  - Configuration moved to `src/config/`
  - Utilities moved to `src/utils/`
  - Scripts moved to `src/scripts/`
- **BREAKING**: All imports now require `src.` prefix
- Upgraded React Router from v6 to v7 in frontend
- Improved test organization into unit/component/system/model categories

### Fixed
- All UI test failures (100% pass rate achieved)
- React warnings and DOM nesting issues
- Python test infrastructure issues
- Import errors after reorganization

### Security
- Removed claude.md from git tracking
- Added claude.md to .gitignore

## [1.0.0] - 2024-06-20

### Added
- Initial release of Music Analyzer V2
- Multi-model support (Parakeet ASR, Phi-4, Gemma)
- Audio file upload and management
- Transcription capabilities
- Lyrics search from multiple sources
- FAISS vector similarity search
- Export functionality in multiple formats
- React/TypeScript frontend
- PostgreSQL with pgvector support
- Redis caching
- MinIO object storage