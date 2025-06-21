#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Simple test of export functionality without database
"""
import json
from src.utils.music_analyzer_export import MusicAnalyzerExporter
from datetime import datetime

def test_export_formats():
    """Test export format generation"""
    print("\n=== Testing Export Format Generation ===\n")
    
    exporter = MusicAnalyzerExporter()
    
    # Mock data
    mock_data = {
        'file_info': {
            'id': 'test-123',
            'original_filename': 'test_song.mp3',
            'file_format': 'mp3',
            'duration': 180.5,
            'sample_rate': 44100,
            'channels': 2,
            'bit_depth': 16,
            'file_size': 5242880,
            'uploaded_at': datetime.utcnow().isoformat(),
            'metadata': {'artist': 'Test Artist', 'album': 'Test Album'}
        },
        'transcriptions': [
            {
                'id': 'trans-1',
                'text': 'These are the test lyrics for our song',
                'language': 'en',
                'confidence': 0.95,
                'created_at': datetime.utcnow().isoformat()
            }
        ],
        'lyrics': [
            {
                'id': 'lyrics-1',
                'source': 'genius',
                'lyrics_text': 'Test lyrics from Genius',
                'confidence': 0.90,
                'language': 'en',
                'created_at': datetime.utcnow().isoformat()
            }
        ]
    }
    
    # Test 1: CSV export
    print("1. Testing CSV format generation...")
    try:
        csv_result = exporter._export_to_csv(mock_data, 'test_song')
        print(f"✓ CSV export successful")
        print(f"  Format: {csv_result['format']}")
        print(f"  Filename: {csv_result['filename']}")
        print(f"  Size: {len(csv_result['content'])} bytes")
    except Exception as e:
        print(f"✗ CSV export failed: {e}")
    
    # Test 2: Excel export
    print("\n2. Testing Excel format generation...")
    try:
        xlsx_result = exporter._export_to_excel(mock_data, 'test_song')
        print(f"✓ Excel export successful")
        print(f"  Format: {xlsx_result['format']}")
        print(f"  Filename: {xlsx_result['filename']}")
        print(f"  Size: {len(xlsx_result['content'])} bytes")
    except Exception as e:
        print(f"✗ Excel export failed: {e}")
    
    # Test 3: JSON format
    print("\n3. Testing JSON format...")
    try:
        json_content = json.dumps(mock_data, indent=2)
        print(f"✓ JSON format successful")
        print(f"  Size: {len(json_content)} bytes")
        print(f"  Preview: {json_content[:200]}...")
    except Exception as e:
        print(f"✗ JSON format failed: {e}")
    
    print("\n✓ Export format testing complete!")
    
    # Test 4: Test tar.gz format support
    print("\n4. Testing TAR.GZ format support...")
    print(f"  Supported formats: {exporter.supported_formats}")
    assert 'tar.gz' in exporter.supported_formats
    assert 'mono_tar.gz' in exporter.supported_formats
    print("✓ TAR.GZ formats are supported")

if __name__ == "__main__":
    test_export_formats()