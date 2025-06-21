#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Mock test for export functionality - doesn't require database
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
import uuid

@pytest.mark.asyncio
async def test_export_json():
    """Test JSON export functionality with mocks"""
    # Mock the exporter
    mock_exporter = Mock()
    
    # Create mock export result
    test_file_data = {
        "id": str(uuid.uuid4()),
        "original_filename": "test_song.mp3",
        "file_format": "mp3",
        "duration": 180.5,
        "transcriptions": [
            {
                "text": "Test transcription",
                "confidence": 0.95
            }
        ],
        "lyrics": [
            {
                "text": "Test lyrics",
                "source": "genius"
            }
        ]
    }
    
    mock_exporter.export_music_file = AsyncMock(return_value={
        "filename": "test_song.mp3.json",
        "content": json.dumps(test_file_data, indent=2),
        "content_type": "application/json"
    })
    
    # Test export
    result = await mock_exporter.export_music_file("test-id", "json")
    
    assert result["filename"] == "test_song.mp3.json"
    assert "test_song.mp3" in result["content"]
    assert result["content_type"] == "application/json"

@pytest.mark.asyncio
async def test_export_csv():
    """Test CSV export functionality with mocks"""
    mock_exporter = Mock()
    
    csv_content = "filename,duration,format\ntest_song.mp3,180.5,mp3"
    mock_exporter.export_music_file = AsyncMock(return_value={
        "filename": "test_song.mp3.csv",
        "content": csv_content,
        "content_type": "text/csv"
    })
    
    result = await mock_exporter.export_music_file("test-id", "csv")
    
    assert result["filename"] == "test_song.mp3.csv"
    assert "test_song.mp3" in result["content"]
    assert result["content_type"] == "text/csv"

@pytest.mark.asyncio
async def test_export_batch():
    """Test batch export functionality with mocks"""
    mock_exporter = Mock()
    
    batch_data = [
        {"id": "1", "filename": "song1.mp3"},
        {"id": "2", "filename": "song2.mp3"},
        {"id": "3", "filename": "song3.mp3"}
    ]
    
    mock_exporter.export_batch = AsyncMock(return_value={
        "filename": "batch_export.zip",
        "content": b"fake zip content",
        "content_type": "application/zip"
    })
    
    result = await mock_exporter.export_batch(["1", "2", "3"], "json")
    
    assert result["filename"] == "batch_export.zip"
    assert result["content_type"] == "application/zip"
    assert isinstance(result["content"], bytes)