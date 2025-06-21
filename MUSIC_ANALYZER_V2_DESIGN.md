# Music Analyzer V2 - Comprehensive Design Document

## 🎯 Project Overview
A professional music analysis system that combines ASR transcription, intelligent search, vector similarity, and real-time streaming capabilities.

## 🏗️ Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Web Frontend  │────▶│   FastAPI Backend │────▶│  AI Models      │
│  (React/Vue)    │     │   (Python)        │     │  - Parakeet ASR │
└─────────────────┘     └──────────────────┘     │  - Gemma 3B     │
                               │                   └─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
            ┌───────▼────────┐   ┌───────▼────────┐
            │  PostgreSQL    │   │   FAISS Index  │
            │  Database      │   │  Vector Search  │
            └────────────────┘   └────────────────┘
                    │                     │
            ┌───────▼────────┐   ┌───────▼────────┐
            │  Redis Cache   │   │  MinIO Storage │
            │  Fast Access   │   │  Audio Files   │
            └────────────────┘   └────────────────┘
```

## 📋 Feature Specifications

### 1. Enhanced Upload System
- **Multi-file Progress**: Real-time progress for each file
- **Drag & Drop**: Visual feedback during upload
- **Format Support**: ALL audio/video formats via FFmpeg
- **Auto-conversion**: Background conversion to optimal format
- **Duplicate Detection**: Hash-based deduplication

### 2. Database Design (PostgreSQL)

```sql
-- Music files table
CREATE TABLE music_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    file_size BIGINT,
    duration FLOAT,
    sample_rate INTEGER,
    channels INTEGER,
    codec VARCHAR(50),
    genre VARCHAR(50),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Transcriptions table
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES music_files(id) ON DELETE CASCADE,
    transcription_text TEXT,
    confidence FLOAT,
    processing_time FLOAT,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    segments JSONB,
    vector_embedding VECTOR(768) -- For pgvector extension
);

-- Lyrics table
CREATE TABLE lyrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES music_files(id) ON DELETE CASCADE,
    source VARCHAR(50), -- 'brave', 'tavily', 'genius', etc.
    lyrics_text TEXT,
    artist VARCHAR(255),
    title VARCHAR(255),
    album VARCHAR(255),
    confidence FLOAT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Search history
CREATE TABLE search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    results JSONB,
    user_ip VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API tokens configuration
CREATE TABLE api_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    encrypted BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Vector Search Implementation (FAISS)

```python
# Vector search architecture
class VectorSearchEngine:
    def __init__(self):
        self.dimension = 768  # Gemma embedding dimension
        self.index = faiss.IndexFlatL2(self.dimension)
        self.id_map = {}  # Maps vector index to file_id
        
    def add_embedding(self, file_id: str, embedding: np.array):
        self.index.add(embedding.reshape(1, -1))
        self.id_map[self.index.ntotal - 1] = file_id
        
    def search(self, query_embedding: np.array, k: int = 10):
        distances, indices = self.index.search(query_embedding.reshape(1, -1), k)
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < self.index.ntotal:
                results.append({
                    'file_id': self.id_map[idx],
                    'distance': float(dist),
                    'similarity': 1 / (1 + float(dist))
                })
        return results
```

### 4. Gemma Model Integration

```python
# Gemma 3B model for enhanced text understanding
class GemmaService:
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained(
            "google/gemma-3n-E4B-it-litert-preview",
            device_map="auto",
            torch_dtype=torch.float16
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            "google/gemma-3n-E4B-it-litert-preview"
        )
        
    def generate_embeddings(self, text: str) -> np.array:
        # Generate embeddings for vector search
        inputs = self.tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            # Use last hidden state as embedding
            embedding = outputs.hidden_states[-1].mean(dim=1).cpu().numpy()
        return embedding
        
    def analyze_lyrics(self, transcription: str, found_lyrics: str) -> dict:
        # Compare and analyze differences
        prompt = f"""Compare these two texts and identify similarities and differences:
        
        Transcription: {transcription}
        
        Official Lyrics: {found_lyrics}
        
        Provide:
        1. Similarity score (0-100)
        2. Key differences
        3. Possible reasons for differences
        """
        
        response = self.generate(prompt)
        return self.parse_analysis(response)
```

### 5. Search Integration

```python
# Brave Search integration
class BraveSearchService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        
    async def search_lyrics(self, artist: str, title: str) -> dict:
        query = f"{artist} {title} lyrics site:genius.com OR site:azlyrics.com"
        params = {
            "q": query,
            "count": 10,
            "search_lang": "en"
        }
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        # Make request and parse results
        
# Tavily Search integration
class TavilySearchService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = TavilyClient(api_key=api_key)
        
    async def search_lyrics(self, query: str) -> dict:
        response = await self.client.search(
            query=f"{query} song lyrics",
            search_depth="advanced",
            include_domains=["genius.com", "azlyrics.com", "lyrics.com"],
            max_results=5
        )
        return self.parse_results(response)
```

### 6. Audio Streaming Service

```python
class AudioStreamingService:
    def __init__(self, storage_backend: str = "minio"):
        self.storage = self._init_storage(storage_backend)
        
    async def stream_audio(self, file_id: str, request: Request):
        # Get file info from database
        file_info = await db.get_file(file_id)
        file_path = file_info['storage_path']
        
        # Handle range requests for seeking
        range_header = request.headers.get('range')
        if range_header:
            return await self._stream_partial(file_path, range_header)
        else:
            return await self._stream_full(file_path)
            
    async def _stream_partial(self, file_path: str, range_header: str):
        # Parse range header and stream requested portion
        start, end = self._parse_range(range_header)
        
        async def iterfile():
            async with aiofiles.open(file_path, 'rb') as f:
                await f.seek(start)
                chunk_size = 64 * 1024
                current = start
                while current < end:
                    remaining = end - current
                    size = min(chunk_size, remaining)
                    data = await f.read(size)
                    if not data:
                        break
                    current += len(data)
                    yield data
                    
        return StreamingResponse(
            iterfile(),
            status_code=206,
            headers={
                'Content-Range': f'bytes {start}-{end}/{total_size}',
                'Accept-Ranges': 'bytes',
                'Content-Type': 'audio/mpeg'
            }
        )
```

### 7. Caching Strategy

```python
# Redis caching for fast access
class CacheService:
    def __init__(self):
        self.redis = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        
    async def get_transcription(self, file_hash: str) -> Optional[dict]:
        key = f"transcription:{file_hash}"
        data = self.redis.get(key)
        return json.loads(data) if data else None
        
    async def set_transcription(self, file_hash: str, data: dict, ttl: int = 86400):
        key = f"transcription:{file_hash}"
        self.redis.setex(key, ttl, json.dumps(data))
        
    async def get_lyrics(self, query: str) -> Optional[dict]:
        key = f"lyrics:{hashlib.md5(query.encode()).hexdigest()}"
        data = self.redis.get(key)
        return json.loads(data) if data else None
```

### 8. Frontend Architecture

```javascript
// Modern React frontend with TypeScript
interface MusicFile {
    id: string;
    filename: string;
    duration: number;
    genre: string;
    transcription?: string;
    lyrics?: string;
    uploadProgress?: number;
}

// Component structure
<MusicAnalyzer>
    <UploadZone onFilesSelected={handleUpload} />
    <UploadProgress files={uploadingFiles} />
    <MusicLibrary>
        <SearchBar onSearch={handleSearch} />
        <FilterControls filters={filters} />
        <MusicGrid files={filteredFiles}>
            <MusicCard 
                file={file}
                onTranscribe={handleTranscribe}
                onPlay={handlePlay}
                onFindLyrics={handleFindLyrics}
            />
        </MusicGrid>
    </MusicLibrary>
    <TranscriptionViewer 
        transcription={selectedTranscription}
        lyrics={selectedLyrics}
        comparison={comparisonResult}
    />
    <AudioPlayer currentTrack={currentTrack} />
    <ConfigurationPanel 
        apiKeys={apiKeys}
        onSave={handleSaveConfig}
    />
</MusicAnalyzer>
```

## 🛠️ Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
1. ✅ Set up PostgreSQL with pgvector extension
2. ✅ Implement database models and migrations
3. ✅ Set up Redis for caching
4. ✅ Configure MinIO for file storage
5. ✅ Create base API structure

### Phase 2: File Management (Week 2)
1. ✅ Enhanced upload system with progress tracking
2. ✅ FFmpeg integration for all formats
3. ✅ Duplicate detection and handling
4. ✅ File organization and metadata extraction
5. ✅ Streaming API implementation

### Phase 3: AI Integration (Week 3)
1. ✅ Deploy Gemma 3B model
2. ✅ Implement embedding generation
3. ✅ Set up FAISS vector search
4. ✅ Integrate with existing Parakeet ASR
5. ✅ Create comparison algorithms

### Phase 4: Search Integration (Week 4)
1. ✅ Brave Search API integration
2. ✅ Tavily Search API integration
3. ✅ Lyrics parsing and cleaning
4. ✅ Result ranking and filtering
5. ✅ Cache implementation

### Phase 5: Frontend Development (Week 5)
1. ✅ Modern React/TypeScript setup
2. ✅ Real-time upload progress
3. ✅ Music library interface
4. ✅ Audio player with seeking
5. ✅ Configuration panel

### Phase 6: Testing & Optimization (Week 6)
1. ✅ Unit tests (>80% coverage)
2. ✅ Integration tests
3. ✅ Performance optimization
4. ✅ Security audit
5. ✅ Documentation

## 🧪 Testing Strategy

### Unit Tests
```python
# Example test structure
class TestTranscriptionService:
    def test_transcribe_audio_success(self):
        # Test successful transcription
        
    def test_transcribe_invalid_format(self):
        # Test error handling
        
    def test_cache_hit_performance(self):
        # Test cache effectiveness
```

### Integration Tests
- Upload → Transcribe → Search → Compare flow
- Multi-user concurrent access
- Large file handling
- API rate limiting

### Performance Benchmarks
- Target: < 2s for transcription start
- Target: < 100ms for search results
- Target: < 50ms for cached responses
- Target: Support 100 concurrent users

## 🗄️ Storage Management System

### Storage Monitor Service

```python
class StorageManager:
    def __init__(self, storage_paths: dict):
        self.original_path = storage_paths['original']
        self.converted_path = storage_paths['converted']
        self.cache_path = storage_paths['cache']
        
    async def get_storage_stats(self) -> dict:
        """Get detailed storage statistics"""
        stats = {
            'original_files': await self._analyze_directory(self.original_path),
            'converted_files': await self._analyze_directory(self.converted_path),
            'cache_files': await self._analyze_directory(self.cache_path),
            'database_size': await self._get_db_size(),
            'faiss_index_size': await self._get_faiss_size(),
            'total_used': 0,
            'available_space': shutil.disk_usage('/').free
        }
        stats['total_used'] = sum(s['total_size'] for s in stats.values() if isinstance(s, dict))
        return stats
        
    async def _analyze_directory(self, path: str) -> dict:
        """Analyze directory for files and sizes"""
        files = []
        total_size = 0
        
        for root, dirs, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                file_stat = os.stat(filepath)
                file_info = {
                    'path': filepath,
                    'filename': filename,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime),
                    'accessed': datetime.fromtimestamp(file_stat.st_atime)
                }
                files.append(file_info)
                total_size += file_stat.st_size
                
        return {
            'count': len(files),
            'total_size': total_size,
            'files': files,
            'average_size': total_size / len(files) if files else 0
        }
```

### Cleanup Service

```python
class CleanupService:
    def __init__(self, db, storage_manager, faiss_index):
        self.db = db
        self.storage = storage_manager
        self.faiss = faiss_index
        
    async def list_cleanup_candidates(self, criteria: dict) -> dict:
        """List files that match cleanup criteria"""
        candidates = {
            'original_files': [],
            'converted_files': [],
            'orphaned_files': [],
            'duplicate_files': []
        }
        
        # Find files older than specified days
        if criteria.get('older_than_days'):
            cutoff_date = datetime.now() - timedelta(days=criteria['older_than_days'])
            
            # Original files
            original_files = await self.db.execute("""
                SELECT f.*, t.transcription_text IS NOT NULL as has_transcription
                FROM music_files f
                LEFT JOIN transcriptions t ON f.id = t.file_id
                WHERE f.uploaded_at < %s
                ORDER BY f.uploaded_at ASC
            """, (cutoff_date,))
            
            candidates['original_files'] = [
                {
                    'id': f['id'],
                    'filename': f['original_filename'],
                    'size': f['file_size'],
                    'uploaded': f['uploaded_at'],
                    'has_transcription': f['has_transcription'],
                    'genre': f['genre'],
                    'storage_path': f['storage_path']
                }
                for f in original_files
            ]
            
        # Find orphaned converted files (no DB entry)
        if criteria.get('find_orphaned'):
            db_files = await self.db.fetch_all("SELECT storage_path FROM music_files")
            db_paths = {f['storage_path'] for f in db_files}
            
            storage_stats = await self.storage.get_storage_stats()
            for file_info in storage_stats['converted_files']['files']:
                if file_info['path'] not in db_paths:
                    candidates['orphaned_files'].append(file_info)
                    
        # Find duplicate files by hash
        if criteria.get('find_duplicates'):
            duplicates = await self.db.execute("""
                SELECT file_hash, COUNT(*) as count, 
                       array_agg(id) as file_ids,
                       array_agg(original_filename) as filenames,
                       SUM(file_size) as total_size
                FROM music_files
                GROUP BY file_hash
                HAVING COUNT(*) > 1
            """)
            
            candidates['duplicate_files'] = [
                {
                    'hash': d['file_hash'],
                    'count': d['count'],
                    'file_ids': d['file_ids'],
                    'filenames': d['filenames'],
                    'potential_savings': d['total_size'] * (d['count'] - 1)
                }
                for d in duplicates
            ]
            
        # Calculate potential space savings
        candidates['potential_savings'] = self._calculate_savings(candidates)
        
        return candidates
        
    async def cleanup_files(self, file_ids: List[str], cleanup_options: dict) -> dict:
        """Clean up selected files and all related data"""
        results = {
            'deleted_files': [],
            'deleted_transcriptions': 0,
            'deleted_vectors': 0,
            'deleted_lyrics': 0,
            'space_freed': 0,
            'errors': []
        }
        
        for file_id in file_ids:
            try:
                # Get file info
                file_info = await self.db.fetch_one(
                    "SELECT * FROM music_files WHERE id = %s", (file_id,)
                )
                
                if not file_info:
                    results['errors'].append(f"File {file_id} not found in database")
                    continue
                    
                # Delete from FAISS index
                if cleanup_options.get('delete_vectors', True):
                    vector_deleted = await self._delete_from_faiss(file_id)
                    if vector_deleted:
                        results['deleted_vectors'] += 1
                        
                # Delete physical files
                if cleanup_options.get('delete_original', True):
                    if os.path.exists(file_info['storage_path']):
                        file_size = os.path.getsize(file_info['storage_path'])
                        os.remove(file_info['storage_path'])
                        results['space_freed'] += file_size
                        
                if cleanup_options.get('delete_converted', True):
                    converted_path = file_info['storage_path'].replace('/original/', '/converted/')
                    converted_path = converted_path.rsplit('.', 1)[0] + '_converted.wav'
                    if os.path.exists(converted_path):
                        file_size = os.path.getsize(converted_path)
                        os.remove(converted_path)
                        results['space_freed'] += file_size
                        
                # Delete from database (cascades to transcriptions, lyrics)
                if cleanup_options.get('delete_db_entries', True):
                    # Count related records before deletion
                    trans_count = await self.db.fetch_one(
                        "SELECT COUNT(*) as count FROM transcriptions WHERE file_id = %s",
                        (file_id,)
                    )
                    lyrics_count = await self.db.fetch_one(
                        "SELECT COUNT(*) as count FROM lyrics WHERE file_id = %s",
                        (file_id,)
                    )
                    
                    results['deleted_transcriptions'] += trans_count['count']
                    results['deleted_lyrics'] += lyrics_count['count']
                    
                    # Delete from database
                    await self.db.execute(
                        "DELETE FROM music_files WHERE id = %s", (file_id,)
                    )
                    
                # Clear from cache
                if cleanup_options.get('clear_cache', True):
                    await self._clear_cache(file_info['file_hash'])
                    
                results['deleted_files'].append({
                    'id': file_id,
                    'filename': file_info['original_filename']
                })
                
            except Exception as e:
                results['errors'].append(f"Error deleting {file_id}: {str(e)}")
                
        return results
        
    async def _delete_from_faiss(self, file_id: str) -> bool:
        """Remove vector from FAISS index"""
        try:
            # Find vector index for file_id
            if file_id in self.faiss.id_map.values():
                # Rebuild index without this vector
                # (FAISS doesn't support deletion, so we rebuild)
                await self.faiss.rebuild_without(file_id)
                return True
        except Exception as e:
            logger.error(f"Error removing from FAISS: {e}")
        return False
```

### Enhanced Storage Management Service

```python
from sqlalchemy import and_, or_, func
from typing import Optional, List, Dict, Tuple
import math

class AdvancedStorageManager:
    def __init__(self, db, storage_paths: dict):
        self.db = db
        self.storage_paths = storage_paths
        
    async def get_paginated_files(
        self,
        page: int = 1,
        per_page: int = 50,
        sort_by: str = 'uploaded_at',
        sort_order: str = 'desc',
        filters: Optional[Dict] = None,
        search_query: Optional[str] = None
    ) -> Dict:
        """Get paginated file list with advanced filtering and sorting"""
        
        # Base query
        query = """
            SELECT 
                f.*,
                t.transcription_text IS NOT NULL as has_transcription,
                l.lyrics_text IS NOT NULL as has_lyrics,
                COALESCE(t.created_at, NULL) as transcribed_at,
                COALESCE(l.fetched_at, NULL) as lyrics_fetched_at,
                -- Calculate total size (original + converted if exists)
                f.file_size + COALESCE(
                    (SELECT file_size FROM converted_files WHERE file_id = f.id), 
                    0
                ) as total_size
            FROM music_files f
            LEFT JOIN transcriptions t ON f.id = t.file_id
            LEFT JOIN lyrics l ON f.id = l.file_id
            WHERE 1=1
        """
        
        params = []
        
        # Apply filters
        if filters:
            if filters.get('genre'):
                query += " AND f.genre = ANY(%s)"
                params.append(filters['genre'] if isinstance(filters['genre'], list) else [filters['genre']])
                
            if filters.get('has_transcription') is not None:
                query += " AND t.transcription_text IS " + ("NOT NULL" if filters['has_transcription'] else "NULL")
                
            if filters.get('has_lyrics') is not None:
                query += " AND l.lyrics_text IS " + ("NOT NULL" if filters['has_lyrics'] else "NULL")
                
            if filters.get('min_size'):
                query += " AND f.file_size >= %s"
                params.append(filters['min_size'])
                
            if filters.get('max_size'):
                query += " AND f.file_size <= %s"
                params.append(filters['max_size'])
                
            if filters.get('date_from'):
                query += " AND f.uploaded_at >= %s"
                params.append(filters['date_from'])
                
            if filters.get('date_to'):
                query += " AND f.uploaded_at <= %s"
                params.append(filters['date_to'])
                
            if filters.get('file_types'):
                extensions = [f".{ft.lower()}" for ft in filters['file_types']]
                query += " AND LOWER(f.original_filename) ~ %s"
                params.append('(' + '|'.join(extensions) + ')$')
                
        # Apply search
        if search_query:
            query += """ 
                AND (
                    f.original_filename ILIKE %s 
                    OR f.genre ILIKE %s
                    OR t.transcription_text ILIKE %s
                    OR l.lyrics_text ILIKE %s
                )
            """
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern] * 4)
            
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as filtered"
        total_count = await self.db.fetch_one(count_query, params)
        total_count = total_count['count']
        
        # Calculate pagination
        total_pages = math.ceil(total_count / per_page)
        offset = (page - 1) * per_page
        
        # Apply sorting
        sort_columns = {
            'filename': 'f.original_filename',
            'size': 'f.file_size',
            'total_size': 'total_size',
            'uploaded_at': 'f.uploaded_at',
            'genre': 'f.genre',
            'duration': 'f.duration',
            'transcribed_at': 'transcribed_at'
        }
        
        sort_column = sort_columns.get(sort_by, 'f.uploaded_at')
        query += f" ORDER BY {sort_column} {sort_order.upper()}"
        
        # Apply pagination
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        # Execute query
        results = await self.db.fetch_all(query, params)
        
        # Format results
        files = []
        for row in results:
            file_data = dict(row)
            
            # Check if converted file exists
            converted_path = self._get_converted_path(file_data['storage_path'])
            if os.path.exists(converted_path):
                file_data['converted_size'] = os.path.getsize(converted_path)
                file_data['has_converted'] = True
            else:
                file_data['converted_size'] = 0
                file_data['has_converted'] = False
                
            files.append(file_data)
            
        return {
            'files': files,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'sort': {
                'by': sort_by,
                'order': sort_order
            }
        }
        
    async def calculate_selection_stats(self, file_ids: List[str]) -> Dict:
        """Calculate statistics for selected files"""
        if not file_ids:
            return {
                'count': 0,
                'total_original_size': 0,
                'total_converted_size': 0,
                'total_size': 0,
                'by_genre': {},
                'by_type': {},
                'with_transcription': 0,
                'with_lyrics': 0
            }
            
        # Get file information
        query = """
            SELECT 
                f.*,
                t.transcription_text IS NOT NULL as has_transcription,
                l.lyrics_text IS NOT NULL as has_lyrics
            FROM music_files f
            LEFT JOIN transcriptions t ON f.id = t.file_id
            LEFT JOIN lyrics l ON f.id = l.file_id
            WHERE f.id = ANY(%s)
        """
        
        results = await self.db.fetch_all(query, (file_ids,))
        
        stats = {
            'count': len(results),
            'total_original_size': 0,
            'total_converted_size': 0,
            'total_size': 0,
            'by_genre': {},
            'by_type': {},
            'with_transcription': 0,
            'with_lyrics': 0,
            'duration_total': 0
        }
        
        for row in results:
            # Original size
            stats['total_original_size'] += row['file_size']
            
            # Check converted size
            converted_path = self._get_converted_path(row['storage_path'])
            if os.path.exists(converted_path):
                converted_size = os.path.getsize(converted_path)
                stats['total_converted_size'] += converted_size
                
            # Genre stats
            genre = row['genre']
            if genre not in stats['by_genre']:
                stats['by_genre'][genre] = {'count': 0, 'size': 0}
            stats['by_genre'][genre]['count'] += 1
            stats['by_genre'][genre]['size'] += row['file_size']
            
            # File type stats
            ext = Path(row['original_filename']).suffix.lower()
            if ext not in stats['by_type']:
                stats['by_type'][ext] = {'count': 0, 'size': 0}
            stats['by_type'][ext]['count'] += 1
            stats['by_type'][ext]['size'] += row['file_size']
            
            # Other stats
            if row['has_transcription']:
                stats['with_transcription'] += 1
            if row['has_lyrics']:
                stats['with_lyrics'] += 1
            if row['duration']:
                stats['duration_total'] += row['duration']
                
        stats['total_size'] = stats['total_original_size'] + stats['total_converted_size']
        
        # Add human-readable sizes
        stats['total_original_size_human'] = self._format_size(stats['total_original_size'])
        stats['total_converted_size_human'] = self._format_size(stats['total_converted_size'])
        stats['total_size_human'] = self._format_size(stats['total_size'])
        stats['duration_total_human'] = self._format_duration(stats['duration_total'])
        
        return stats
        
    async def get_storage_analytics(self) -> Dict:
        """Get comprehensive storage analytics"""
        analytics = {
            'by_genre': {},
            'by_file_type': {},
            'by_month': {},
            'largest_files': [],
            'oldest_files': [],
            'orphaned_files': [],
            'duplicate_files': [],
            'storage_trends': []
        }
        
        # Genre distribution
        genre_query = """
            SELECT 
                genre,
                COUNT(*) as count,
                SUM(file_size) as total_size,
                AVG(file_size) as avg_size,
                SUM(duration) as total_duration
            FROM music_files
            GROUP BY genre
            ORDER BY total_size DESC
        """
        genre_results = await self.db.fetch_all(genre_query)
        
        for row in genre_results:
            analytics['by_genre'][row['genre']] = {
                'count': row['count'],
                'total_size': row['total_size'],
                'total_size_human': self._format_size(row['total_size']),
                'avg_size': row['avg_size'],
                'avg_size_human': self._format_size(row['avg_size']),
                'total_duration': row['total_duration'],
                'total_duration_human': self._format_duration(row['total_duration'])
            }
            
        # File type distribution
        type_query = """
            SELECT 
                LOWER(SUBSTRING(original_filename FROM '\.([^.]+)$')) as file_type,
                COUNT(*) as count,
                SUM(file_size) as total_size,
                AVG(file_size) as avg_size
            FROM music_files
            GROUP BY file_type
            ORDER BY total_size DESC
        """
        type_results = await self.db.fetch_all(type_query)
        
        for row in type_results:
            if row['file_type']:
                analytics['by_file_type'][row['file_type']] = {
                    'count': row['count'],
                    'total_size': row['total_size'],
                    'total_size_human': self._format_size(row['total_size']),
                    'avg_size': row['avg_size'],
                    'avg_size_human': self._format_size(row['avg_size'])
                }
                
        # Storage trends by month
        trend_query = """
            SELECT 
                DATE_TRUNC('month', uploaded_at) as month,
                COUNT(*) as files_added,
                SUM(file_size) as size_added
            FROM music_files
            WHERE uploaded_at >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY month
            ORDER BY month DESC
        """
        trend_results = await self.db.fetch_all(trend_query)
        
        for row in trend_results:
            analytics['by_month'][row['month'].strftime('%Y-%m')] = {
                'files_added': row['files_added'],
                'size_added': row['size_added'],
                'size_added_human': self._format_size(row['size_added'])
            }
            
        # Largest files
        largest_query = """
            SELECT id, original_filename, file_size, genre, uploaded_at
            FROM music_files
            ORDER BY file_size DESC
            LIMIT 20
        """
        largest_results = await self.db.fetch_all(largest_query)
        
        analytics['largest_files'] = [
            {
                'id': row['id'],
                'filename': row['original_filename'],
                'size': row['file_size'],
                'size_human': self._format_size(row['file_size']),
                'genre': row['genre'],
                'uploaded_at': row['uploaded_at'].isoformat()
            }
            for row in largest_results
        ]
        
        # Check for orphaned files
        db_files = await self.db.fetch_all("SELECT storage_path FROM music_files")
        db_paths = {row['storage_path'] for row in db_files}
        
        for storage_type in ['original', 'converted']:
            storage_path = self.storage_paths[storage_type]
            if os.path.exists(storage_path):
                for root, dirs, files in os.walk(storage_path):
                    for file in files:
                        filepath = os.path.join(root, file)
                        if filepath not in db_paths:
                            file_stat = os.stat(filepath)
                            analytics['orphaned_files'].append({
                                'path': filepath,
                                'size': file_stat.st_size,
                                'size_human': self._format_size(file_stat.st_size),
                                'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                'type': storage_type
                            })
                            
        return analytics
        
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
        
    def _format_duration(self, seconds: float) -> str:
        """Format seconds to human readable duration"""
        if not seconds:
            return "0s"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if secs or not parts:
            parts.append(f"{secs}s")
            
        return " ".join(parts)
```

### Storage Management API Endpoints

```python
@app.get("/storage/stats")
async def get_storage_stats(
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Get current storage statistics"""
    storage_manager = StorageManager({
        'original': MUSIC_BASE_DIR / 'original',
        'converted': MUSIC_BASE_DIR / 'converted',
        'cache': MUSIC_BASE_DIR / 'cache'
    })
    
    stats = await storage_manager.get_storage_stats()
    
    # Add human-readable sizes
    for key in stats:
        if isinstance(stats[key], dict) and 'total_size' in stats[key]:
            stats[key]['total_size_human'] = humanize.naturalsize(stats[key]['total_size'])
            
    stats['available_space_human'] = humanize.naturalsize(stats['available_space'])
    stats['total_used_human'] = humanize.naturalsize(stats['total_used'])
    
    return stats

@app.post("/storage/cleanup/preview")
async def preview_cleanup(
    criteria: dict,
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Preview files that would be cleaned up based on criteria"""
    cleanup_service = CleanupService(db, storage_manager, faiss_index)
    candidates = await cleanup_service.list_cleanup_candidates(criteria)
    return candidates

@app.post("/storage/cleanup/execute")
async def execute_cleanup(
    file_ids: List[str],
    options: dict = {
        'delete_original': True,
        'delete_converted': True,
        'delete_vectors': True,
        'delete_db_entries': True,
        'clear_cache': True
    },
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Execute cleanup for selected files"""
    cleanup_service = CleanupService(db, storage_manager, faiss_index)
    results = await cleanup_service.cleanup_files(file_ids, options)
    
    # Log cleanup action
    await db.execute("""
        INSERT INTO cleanup_log (action, file_count, space_freed, details, performed_at)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
    """, ('manual_cleanup', len(file_ids), results['space_freed'], json.dumps(results)))
    
    return results

@app.get("/storage/files/orphaned")
async def find_orphaned_files(
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Find files on disk that don't have database entries"""
    # Implementation to find orphaned files
    pass

@app.post("/storage/optimize")
async def optimize_storage(
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Run storage optimization (compress, deduplicate, etc.)"""
    # Implementation for storage optimization
    pass
```

### Frontend Storage Management Interface

```typescript
// Storage management component
interface StorageStats {
    original_files: DirectoryStats;
    converted_files: DirectoryStats;
    cache_files: DirectoryStats;
    database_size: number;
    faiss_index_size: number;
    total_used: number;
    available_space: number;
}

interface CleanupCandidate {
    id: string;
    filename: string;
    size: number;
    uploaded: Date;
    has_transcription: boolean;
    selected?: boolean;
}

const StorageManager: React.FC = () => {
    const [stats, setStats] = useState<StorageStats | null>(null);
    const [candidates, setCandidates] = useState<CleanupCandidate[]>([]);
    const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
    const [cleanupOptions, setCleanupOptions] = useState({
        delete_original: true,
        delete_converted: true,
        delete_vectors: true,
        delete_db_entries: true,
        clear_cache: true
    });
    
    return (
        <div className="storage-manager">
            <StorageOverview stats={stats} />
            
            <CleanupCriteria onSearch={handleSearchCandidates}>
                <CriteriaOption 
                    label="Files older than"
                    type="days"
                    value={olderThanDays}
                    onChange={setOlderThanDays}
                />
                <CriteriaOption 
                    label="Find orphaned files"
                    type="checkbox"
                    value={findOrphaned}
                    onChange={setFindOrphaned}
                />
                <CriteriaOption 
                    label="Find duplicates"
                    type="checkbox"
                    value={findDuplicates}
                    onChange={setFindDuplicates}
                />
            </CleanupCriteria>
            
            <FileList 
                files={candidates}
                selectedFiles={selectedFiles}
                onSelectionChange={handleSelectionChange}
            />
            
            <CleanupOptions 
                options={cleanupOptions}
                onChange={setCleanupOptions}
            />
            
            <CleanupActions
                selectedCount={selectedFiles.size}
                potentialSavings={calculateSavings(selectedFiles)}
                onCleanup={handleCleanup}
                onCancel={handleCancel}
            />
        </div>
    );
};
```

### Download & Export Service

```python
import tarfile
import zipfile
from io import BytesIO
import json
import csv

class ExportService:
    def __init__(self, storage_paths: dict, db):
        self.storage_paths = storage_paths
        self.db = db
        
    async def export_single_file(self, file_id: str, export_type: str) -> StreamingResponse:
        """Export a single file (original, converted, or transcription)"""
        file_info = await self.db.fetch_one(
            "SELECT * FROM music_files WHERE id = %s", (file_id,)
        )
        
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
            
        if export_type == 'original':
            file_path = file_info['storage_path']
            filename = file_info['original_filename']
            content_type = self._get_content_type(filename)
            
        elif export_type == 'converted':
            file_path = self._get_converted_path(file_info['storage_path'])
            filename = f"{Path(file_info['original_filename']).stem}_mono_16khz.wav"
            content_type = 'audio/wav'
            
        elif export_type == 'transcription':
            # Get transcription from database
            trans = await self.db.fetch_one(
                "SELECT * FROM transcriptions WHERE file_id = %s ORDER BY created_at DESC",
                (file_id,)
            )
            if not trans:
                raise HTTPException(status_code=404, detail="No transcription found")
                
            # Create text file
            content = self._format_transcription(file_info, trans)
            return Response(
                content=content,
                media_type='text/plain',
                headers={
                    'Content-Disposition': f'attachment; filename="{Path(file_info["original_filename"]).stem}_transcription.txt"'
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid export type")
            
        # Stream file
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
            
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    async def export_multiple_files(self, file_ids: List[str], export_options: dict) -> StreamingResponse:
        """Export multiple files as compressed archive"""
        # Create in-memory archive
        archive_buffer = BytesIO()
        
        if export_options.get('format', 'tar.gz') == 'tar.gz':
            archive = tarfile.open(fileobj=archive_buffer, mode='w:gz')
        else:
            archive = zipfile.ZipFile(archive_buffer, 'w', zipfile.ZIP_DEFLATED)
            
        # Add metadata file
        metadata = {
            'export_date': datetime.now().isoformat(),
            'file_count': len(file_ids),
            'files': []
        }
        
        for file_id in file_ids:
            try:
                file_info = await self.db.fetch_one(
                    "SELECT * FROM music_files WHERE id = %s", (file_id,)
                )
                
                if not file_info:
                    continue
                    
                file_metadata = {
                    'id': file_id,
                    'filename': file_info['original_filename'],
                    'genre': file_info['genre'],
                    'duration': file_info['duration'],
                    'included': []
                }
                
                # Create folder structure
                base_folder = f"{file_info['genre']}/{Path(file_info['original_filename']).stem}"
                
                # Add original file
                if export_options.get('include_original', True):
                    if os.path.exists(file_info['storage_path']):
                        if isinstance(archive, tarfile.TarFile):
                            archive.add(
                                file_info['storage_path'],
                                arcname=f"{base_folder}/original/{file_info['original_filename']}"
                            )
                        else:
                            archive.write(
                                file_info['storage_path'],
                                arcname=f"{base_folder}/original/{file_info['original_filename']}"
                            )
                        file_metadata['included'].append('original')
                        
                # Add converted file
                if export_options.get('include_converted', False):
                    converted_path = self._get_converted_path(file_info['storage_path'])
                    if os.path.exists(converted_path):
                        converted_name = f"{Path(file_info['original_filename']).stem}_mono_16khz.wav"
                        if isinstance(archive, tarfile.TarFile):
                            archive.add(
                                converted_path,
                                arcname=f"{base_folder}/converted/{converted_name}"
                            )
                        else:
                            archive.write(
                                converted_path,
                                arcname=f"{base_folder}/converted/{converted_name}"
                            )
                        file_metadata['included'].append('converted')
                        
                # Add transcription
                if export_options.get('include_transcription', True):
                    trans = await self.db.fetch_one(
                        "SELECT * FROM transcriptions WHERE file_id = %s ORDER BY created_at DESC",
                        (file_id,)
                    )
                    
                    if trans:
                        trans_content = self._format_transcription(file_info, trans)
                        trans_filename = f"{Path(file_info['original_filename']).stem}_transcription.txt"
                        
                        if isinstance(archive, tarfile.TarFile):
                            trans_info = tarfile.TarInfo(name=f"{base_folder}/transcription/{trans_filename}")
                            trans_info.size = len(trans_content.encode())
                            archive.addfile(trans_info, BytesIO(trans_content.encode()))
                        else:
                            archive.writestr(
                                f"{base_folder}/transcription/{trans_filename}",
                                trans_content
                            )
                        file_metadata['included'].append('transcription')
                        
                # Add lyrics if available
                if export_options.get('include_lyrics', True):
                    lyrics = await self.db.fetch_one(
                        "SELECT * FROM lyrics WHERE file_id = %s ORDER BY fetched_at DESC",
                        (file_id,)
                    )
                    
                    if lyrics:
                        lyrics_content = self._format_lyrics(file_info, lyrics)
                        lyrics_filename = f"{Path(file_info['original_filename']).stem}_lyrics.txt"
                        
                        if isinstance(archive, tarfile.TarFile):
                            lyrics_info = tarfile.TarInfo(name=f"{base_folder}/lyrics/{lyrics_filename}")
                            lyrics_info.size = len(lyrics_content.encode())
                            archive.addfile(lyrics_info, BytesIO(lyrics_content.encode()))
                        else:
                            archive.writestr(
                                f"{base_folder}/lyrics/{lyrics_filename}",
                                lyrics_content
                            )
                        file_metadata['included'].append('lyrics')
                        
                metadata['files'].append(file_metadata)
                
            except Exception as e:
                logger.error(f"Error exporting file {file_id}: {e}")
                continue
                
        # Add metadata file to archive
        metadata_content = json.dumps(metadata, indent=2)
        if isinstance(archive, tarfile.TarFile):
            metadata_info = tarfile.TarInfo(name="export_metadata.json")
            metadata_info.size = len(metadata_content.encode())
            archive.addfile(metadata_info, BytesIO(metadata_content.encode()))
        else:
            archive.writestr("export_metadata.json", metadata_content)
            
        # Close archive
        archive.close()
        
        # Prepare response
        archive_buffer.seek(0)
        filename = f"music_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{'tar.gz' if export_options.get('format') == 'tar.gz' else 'zip'}"
        
        return StreamingResponse(
            archive_buffer,
            media_type='application/x-gzip' if export_options.get('format') == 'tar.gz' else 'application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    async def export_transcriptions_csv(self, file_ids: List[str] = None) -> StreamingResponse:
        """Export transcriptions as CSV"""
        output = BytesIO()
        writer = csv.writer(io.TextIOWrapper(output, encoding='utf-8', newline=''))
        
        # Write header
        writer.writerow([
            'File ID', 'Filename', 'Genre', 'Duration', 'Transcription', 
            'Confidence', 'Processing Time', 'Model Version', 'Created At'
        ])
        
        # Query transcriptions
        if file_ids:
            query = """
                SELECT f.*, t.*
                FROM music_files f
                JOIN transcriptions t ON f.id = t.file_id
                WHERE f.id = ANY(%s)
                ORDER BY t.created_at DESC
            """
            results = await self.db.fetch_all(query, (file_ids,))
        else:
            query = """
                SELECT f.*, t.*
                FROM music_files f
                JOIN transcriptions t ON f.id = t.file_id
                ORDER BY t.created_at DESC
            """
            results = await self.db.fetch_all(query)
            
        # Write data
        for row in results:
            writer.writerow([
                row['id'],
                row['original_filename'],
                row['genre'],
                row['duration'],
                row['transcription_text'],
                row['confidence'],
                row['processing_time'],
                row['model_version'],
                row['created_at'].isoformat()
            ])
            
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="transcriptions_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            }
        )
        
    def _format_transcription(self, file_info: dict, trans: dict) -> str:
        """Format transcription for export"""
        return f"""Transcription for: {file_info['original_filename']}
Generated: {trans['created_at'].isoformat()}
Model: {trans.get('model_version', 'Parakeet TDT')}
Processing Time: {trans['processing_time']:.2f}s
Confidence: {trans.get('confidence', 'N/A')}

{'='*60}

{trans['transcription_text']}

{'='*60}

File Details:
- Genre: {file_info['genre']}
- Duration: {file_info['duration']:.2f}s
- Sample Rate: {file_info['sample_rate']}Hz
- Channels: {file_info['channels']}
- Codec: {file_info['codec']}
- File Hash: {file_info['file_hash']}
"""

    def _format_lyrics(self, file_info: dict, lyrics: dict) -> str:
        """Format lyrics for export"""
        return f"""Lyrics for: {file_info['original_filename']}
Source: {lyrics['source']}
Fetched: {lyrics['fetched_at'].isoformat()}

Artist: {lyrics.get('artist', 'Unknown')}
Title: {lyrics.get('title', 'Unknown')}
Album: {lyrics.get('album', 'Unknown')}

{'='*60}

{lyrics['lyrics_text']}

{'='*60}
"""
```

### Export API Endpoints

```python
@app.get("/export/file/{file_id}/{export_type}")
async def export_single_file(
    file_id: str,
    export_type: str = Query(..., regex="^(original|converted|transcription)$"),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Download a single file (original, converted, or transcription)"""
    export_service = ExportService(storage_paths, db)
    return await export_service.export_single_file(file_id, export_type)

@app.post("/export/batch")
async def export_batch(
    file_ids: List[str],
    options: dict = Body(default={
        'format': 'tar.gz',  # or 'zip'
        'include_original': True,
        'include_converted': False,
        'include_transcription': True,
        'include_lyrics': True
    }),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Export multiple files as compressed archive"""
    export_service = ExportService(storage_paths, db)
    return await export_service.export_multiple_files(file_ids, options)

@app.get("/export/transcriptions/csv")
async def export_transcriptions_csv(
    file_ids: Optional[List[str]] = Query(None),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Export transcriptions as CSV file"""
    export_service = ExportService(storage_paths, db)
    return await export_service.export_transcriptions_csv(file_ids)

@app.post("/export/search-results")
async def export_search_results(
    search_query: str,
    export_format: str = "json",  # json, csv, txt
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Export search results in various formats"""
    # Search implementation
    results = await search_service.search(search_query)
    
    if export_format == "json":
        return JSONResponse(
            content=results,
            headers={
                'Content-Disposition': f'attachment; filename="search_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
            }
        )
    elif export_format == "csv":
        # Convert to CSV
        pass
    elif export_format == "txt":
        # Convert to text format
        pass
```

### Frontend Export Interface

```typescript
// Export component
interface ExportOptions {
    format: 'tar.gz' | 'zip';
    include_original: boolean;
    include_converted: boolean;
    include_transcription: boolean;
    include_lyrics: boolean;
}

const ExportManager: React.FC = () => {
    const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
    const [exportOptions, setExportOptions] = useState<ExportOptions>({
        format: 'tar.gz',
        include_original: true,
        include_converted: false,
        include_transcription: true,
        include_lyrics: true
    });
    const [isExporting, setIsExporting] = useState(false);
    
    const handleSingleDownload = async (fileId: string, type: 'original' | 'converted' | 'transcription') => {
        try {
            const response = await fetch(`/export/file/${fileId}/${type}`, {
                headers: {
                    'Authorization': `Basic ${btoa(`${username}:${password}`)}`
                }
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = getFilenameFromResponse(response);
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
        } catch (error) {
            console.error('Download failed:', error);
            showNotification('Download failed', 'error');
        }
    };
    
    const handleBatchExport = async () => {
        if (selectedFiles.size === 0) {
            showNotification('Please select files to export', 'warning');
            return;
        }
        
        setIsExporting(true);
        
        try {
            const response = await fetch('/export/batch', {
                method: 'POST',
                headers: {
                    'Authorization': `Basic ${btoa(`${username}:${password}`)}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    file_ids: Array.from(selectedFiles),
                    options: exportOptions
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `music_export_${new Date().toISOString().slice(0, 10)}.${exportOptions.format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                showNotification(`Exported ${selectedFiles.size} files successfully`, 'success');
            }
        } catch (error) {
            console.error('Batch export failed:', error);
            showNotification('Export failed', 'error');
        } finally {
            setIsExporting(false);
        }
    };
    
    return (
        <div className="export-manager">
            <div className="export-options">
                <h3>Export Options</h3>
                
                <div className="format-selector">
                    <label>Archive Format:</label>
                    <select 
                        value={exportOptions.format} 
                        onChange={(e) => setExportOptions({...exportOptions, format: e.target.value as 'tar.gz' | 'zip'})}
                    >
                        <option value="tar.gz">TAR.GZ (Compressed)</option>
                        <option value="zip">ZIP</option>
                    </select>
                </div>
                
                <div className="content-options">
                    <label>
                        <input 
                            type="checkbox" 
                            checked={exportOptions.include_original}
                            onChange={(e) => setExportOptions({...exportOptions, include_original: e.target.checked})}
                        />
                        Include Original Files
                    </label>
                    
                    <label>
                        <input 
                            type="checkbox" 
                            checked={exportOptions.include_converted}
                            onChange={(e) => setExportOptions({...exportOptions, include_converted: e.target.checked})}
                        />
                        Include Converted (Mono 16kHz) Files
                    </label>
                    
                    <label>
                        <input 
                            type="checkbox" 
                            checked={exportOptions.include_transcription}
                            onChange={(e) => setExportOptions({...exportOptions, include_transcription: e.target.checked})}
                        />
                        Include Transcriptions
                    </label>
                    
                    <label>
                        <input 
                            type="checkbox" 
                            checked={exportOptions.include_lyrics}
                            onChange={(e) => setExportOptions({...exportOptions, include_lyrics: e.target.checked})}
                        />
                        Include Lyrics (if available)
                    </label>
                </div>
            </div>
            
            <div className="export-actions">
                <button 
                    onClick={handleBatchExport}
                    disabled={selectedFiles.size === 0 || isExporting}
                    className="btn-primary"
                >
                    {isExporting ? 'Exporting...' : `Export ${selectedFiles.size} Files`}
                </button>
                
                <button 
                    onClick={() => exportTranscriptionsCSV()}
                    className="btn-secondary"
                >
                    Export All Transcriptions (CSV)
                </button>
            </div>
            
            <div className="quick-downloads">
                {/* Per-file download buttons in the file list */}
                <div className="download-menu">
                    <button onClick={() => handleSingleDownload(fileId, 'original')}>
                        📥 Original
                    </button>
                    <button onClick={() => handleSingleDownload(fileId, 'converted')}>
                        📥 Mono 16kHz
                    </button>
                    <button onClick={() => handleSingleDownload(fileId, 'transcription')}>
                        📥 Transcription
                    </button>
                </div>
            </div>
        </div>
    );
};
```

### Database Schema Addition

```sql
-- Cleanup log table
CREATE TABLE cleanup_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action VARCHAR(50) NOT NULL,
    file_count INTEGER,
    space_freed BIGINT,
    details JSONB,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    performed_by VARCHAR(255)
);

-- Storage stats cache
CREATE TABLE storage_stats (
    id SERIAL PRIMARY KEY,
    stats_data JSONB NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add index for faster cleanup queries
CREATE INDEX idx_music_files_uploaded_at ON music_files(uploaded_at);
CREATE INDEX idx_music_files_file_hash ON music_files(file_hash);
```

## 🔒 Security Considerations

1. **API Key Encryption**: Store API keys encrypted in database
2. **Rate Limiting**: Implement per-IP and per-user limits
3. **File Validation**: Strict file type and size validation
4. **SQL Injection**: Use parameterized queries
5. **XSS Prevention**: Sanitize all user inputs
6. **CORS Configuration**: Restrict to known origins

## 📊 Monitoring & Analytics

1. **Prometheus Metrics**
   - Request rates
   - Processing times
   - Error rates
   - Resource usage

2. **Logging Strategy**
   - Structured JSON logs
   - Log aggregation with ELK
   - Error tracking with Sentry

3. **Performance Monitoring**
   - APM with DataDog/NewRelic
   - Database query optimization
   - Cache hit rates

## 🚀 Deployment Architecture

```yaml
# Docker Compose setup
version: '3.8'
services:
  api:
    build: ./api
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
      - minio
      
  postgres:
    image: pgvector/pgvector:pg15
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
      
  minio:
    image: minio/minio
    command: server /data
    volumes:
      - minio_data:/data
      
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "443:443"
```

## 📈 Success Metrics

1. **Performance**
   - 95th percentile response time < 1s
   - Transcription accuracy > 90%
   - Search relevance > 80%

2. **Reliability**
   - 99.9% uptime
   - Zero data loss
   - Graceful degradation

3. **User Experience**
   - Upload success rate > 99%
   - Search satisfaction > 85%
   - Player buffering < 1%

---

This design provides a solid foundation for building a professional music analysis system with all requested features.