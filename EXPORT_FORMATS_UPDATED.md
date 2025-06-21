# Updated Export Functionality

## Overview
The Music Analyzer export functionality has been enhanced to support tar.gz exports for both original uploaded files and processed mono files.

## New Export Formats

### 1. **tar.gz** - Original Files Archive
Exports the original uploaded audio files (FLAC, MP3, etc.) in a compressed tar.gz archive.

**Single File Export:**
```bash
GET /api/v2/export/{file_id}?format=tar.gz
```
- Contains: Original audio file with its original filename

**Batch Export:**
```bash
POST /api/v2/export/batch
{
  "file_ids": ["id1", "id2", "id3"],
  "format": "tar.gz"
}
```
- Contains: All original audio files with their original filenames

### 2. **mono_tar.gz** - Mono Files with Metadata
Exports processed mono audio files along with all metadata, transcriptions, and lyrics in a structured tar.gz archive.

**Single File Export:**
```bash
GET /api/v2/export/{file_id}?format=mono_tar.gz
```

Archive structure:
```
song_name/
├── mono.wav              # Processed mono audio file
├── metadata.json         # Complete metadata
├── transcription_1.txt   # Transcription with language and confidence
├── transcription_2.txt   # Additional transcriptions if any
├── lyrics_genius_1.txt   # Lyrics from various sources
└── lyrics_brave_2.txt
```

**Batch Export:**
```bash
POST /api/v2/export/batch
{
  "file_ids": ["id1", "id2", "id3"],
  "format": "mono_tar.gz"
}
```

Archive structure:
```
song1_name/
├── mono.wav
├── metadata.json
├── transcription_1.txt
└── lyrics_genius_1.txt

song2_name/
├── mono.wav
├── metadata.json
├── transcription_1.txt
└── lyrics_brave_1.txt

song3_name/
├── mono.wav
├── metadata.json
└── transcription_1.txt
```

## All Supported Export Formats

1. **json** - Complete data in JSON format
2. **csv** - Data in CSV files (zipped if multiple tables)
3. **xlsx** - Excel workbook with multiple sheets
4. **zip** - Complete export with JSON data and original audio
5. **tar.gz** - Original audio files only (compressed)
6. **mono_tar.gz** - Mono audio files with all metadata (compressed)

## Usage Examples

### Export single file as tar.gz
```bash
curl -u user:pass \
  "http://localhost:8000/api/v2/export/file-123?format=tar.gz" \
  -o original_files.tar.gz
```

### Export batch as mono tar.gz
```bash
curl -u user:pass \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"file_ids": ["id1", "id2"], "format": "mono_tar.gz"}' \
  "http://localhost:8000/api/v2/export/batch" \
  -o mono_files_complete.tar.gz
```

### Extract tar.gz archive
```bash
# List contents
tar -tzf original_files.tar.gz

# Extract all files
tar -xzf original_files.tar.gz

# Extract to specific directory
tar -xzf mono_files_complete.tar.gz -C /path/to/extract/
```

## Implementation Notes

- The exporter checks local storage first before falling back to MinIO
- Mono files are expected in the `/processed/` directory with `.mono.wav` extension
- Archives use gzip compression for efficient file sizes
- Temporary files are properly cleaned up after export
- Large exports may take time - consider implementing progress tracking for production use