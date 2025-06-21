-- Music Analyzer V2 Database Schema
-- PostgreSQL with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

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
    vector_embedding vector(768) -- For pgvector extension
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

-- Create indexes for better performance
CREATE INDEX idx_music_files_uploaded_at ON music_files(uploaded_at);
CREATE INDEX idx_music_files_file_hash ON music_files(file_hash);
CREATE INDEX idx_music_files_genre ON music_files(genre);
CREATE INDEX idx_transcriptions_file_id ON transcriptions(file_id);
CREATE INDEX idx_lyrics_file_id ON lyrics(file_id);
CREATE INDEX idx_search_history_created_at ON search_history(created_at);

-- Create vector similarity index
CREATE INDEX idx_transcriptions_vector ON transcriptions USING hnsw (vector_embedding vector_cosine_ops);

-- Grant permissions to music_user
GRANT ALL ON ALL TABLES IN SCHEMA public TO music_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO music_user;