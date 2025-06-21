# Export Functionality Update Summary

## What Was Added

### New Export Formats
1. **tar.gz** - Exports original uploaded audio files in compressed tar.gz format
2. **mono_tar.gz** - Exports processed mono audio files with all metadata in structured tar.gz format

### Implementation Details

#### Files Modified:
1. **music_analyzer_export.py**
   - Added `tar.gz` and `mono_tar.gz` to supported formats
   - Implemented `_export_original_files_tar_gz()` method
   - Implemented `_export_mono_files_tar_gz()` method
   - Implemented `_export_mono_files_tar_gz_batch()` method
   - Fixed field name issues (transcription_text vs text)
   - Updated to use storage_path instead of minio_path

2. **music_analyzer_api.py**
   - Updated export endpoints to include new formats in documentation
   - Added tar.gz and mono_tar.gz to format options

#### Key Features:
- Checks local storage first before falling back to MinIO
- Supports both single file and batch exports
- Mono files include all metadata, transcriptions, and lyrics
- Proper cleanup of temporary files
- Structured directory format for mono exports

### API Usage

#### Export original files:
```bash
GET /api/v2/export/{file_id}?format=tar.gz
```

#### Export mono files with metadata:
```bash
GET /api/v2/export/{file_id}?format=mono_tar.gz
```

#### Batch export:
```bash
POST /api/v2/export/batch
{
  "file_ids": ["id1", "id2"],
  "format": "tar.gz"  # or "mono_tar.gz"
}
```

### Archive Structure

**tar.gz format:**
- Contains original uploaded files with original filenames

**mono_tar.gz format:**
```
song_name/
├── mono.wav              # Processed mono audio
├── metadata.json         # Complete metadata
├── transcription_1.txt   # Transcriptions
└── lyrics_source_1.txt   # Lyrics from various sources
```

## Status
Export functionality has been successfully updated with tar.gz support for both original and mono files as requested.