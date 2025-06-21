# Import Structure Updates

This document describes the updated import structure after moving files to the new directory layout.

## Directory Structure

```
src/
├── api/
│   └── music_analyzer_api.py
├── config/
│   └── music_analyzer_config.py
├── models/
│   ├── music_analyzer_models.py
│   ├── gemma_manager.py
│   └── multi_model_manager.py
├── managers/
│   ├── faiss_manager.py
│   ├── lyrics_search_manager.py
│   └── storage_manager.py
├── utils/
│   ├── music_analyzer_export.py
│   └── lyrics_search_enhanced.py
└── scripts/
    └── (various scripts)
```

## Import Changes

### Old Import Style
```python
from music_analyzer_config import DATABASE_URL
from music_analyzer_models import MusicFile
from faiss_manager import FAISSManager
```

### New Import Style
```python
from src.config.music_analyzer_config import DATABASE_URL
from src.models.music_analyzer_models import MusicFile
from src.managers.faiss_manager import FAISSManager
```

## Running the Application

### API Server
To run the main API server:
```bash
python run_api.py
```

### Scripts
To run any script with proper imports:
```bash
python run_script.py src/scripts/initialize_database.py
```

## Updated Files

The following files have been updated with new import paths:

### Main API
- `src/api/music_analyzer_api.py`

### Managers
- `src/managers/storage_manager.py`

### Utils
- `src/utils/music_analyzer_export.py`
- `src/utils/music_analyzer_v2_integration.py`
- `src/utils/lyrics_search_enhanced.py`

### Scripts
- `src/scripts/initialize_database.py`
- `src/scripts/test_tar_export.py`
- `src/scripts/download_and_test_models.py`
- `src/config/model_config_interface.py`

### Tests
- `tests/system/test_music_analyzer_api.py`
- `tests/component/test_music_analyzer.py`
- `tests/unit/test_faiss_integration.py`
- `tests/unit/test_lyrics_search.py`
- `tests/unit/test_export_simple.py`
- `tests/model/test_all_models.py`
- `tests/model/test_gemma_in_manager.py`
- `tests/model/test_model_manager.py`
- `tests/model/test_models_integration.py`
- `tests/model/test_multi_model_gemma.py`
- `tests/model/test_gemma_integration.py`

## Import Resolution

When running scripts directly, ensure the project root is in the Python path:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

Or use the provided runner scripts which handle this automatically.