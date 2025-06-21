#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test Music Analyzer with existing catalog files
"""
import requests
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "parakeet"
PASSWORD = "Q7+sKsoPWJH5vuulfY+RuQSmUyZj3jBa09Ql5om32hI="

def test_existing_files():
    """Test transcription and search with existing catalog files"""
    print("🎵 Testing Music Analyzer with Existing Files")
    print("=" * 70)
    
    session = requests.Session()
    session.auth = (USERNAME, PASSWORD)
    
    # 1. Get catalog
    print("\n1️⃣ Getting existing catalog...")
    response = session.get(f"{BASE_URL}/music/catalog")
    
    if response.status_code == 200:
        catalog = response.json()
        print(f"✓ Found {len(catalog['files'])} files in catalog")
        
        # Get FLAC files
        flac_files = []
        for filepath, info in catalog['files'].items():
            if filepath.endswith('.flac'):
                flac_files.append({
                    'filepath': filepath,
                    'filename': Path(filepath).name,
                    'genre': info['genre'],
                    'duration': info['duration']
                })
        
        print(f"✓ Found {len(flac_files)} FLAC files")
        
        # 2. Test transcription on first 3 FLAC files
        print("\n2️⃣ Testing transcription...")
        transcribed = []
        
        for file_info in flac_files[:3]:
            print(f"\nTranscribing: {file_info['filename']}")
            
            response = session.post(
                f"{BASE_URL}/music/transcribe",
                json={"filepath": file_info['filepath']}
            )
            
            if response.status_code == 200:
                data = response.json()
                transcribed.append({
                    'filename': file_info['filename'],
                    'text': data.get('text', ''),
                    'processing_time': data.get('processing_time', 0),
                    'audio_duration': data.get('audio_duration', 0)
                })
                
                print(f"✓ Success!")
                print(f"  Processing time: {data['processing_time']:.1f}s")
                print(f"  Speed: {data['audio_duration']/data['processing_time']:.1f}x realtime")
                if data['text']:
                    print(f"  Text preview: {data['text'][:100]}...")
                else:
                    print(f"  No text detected")
            else:
                print(f"✗ Failed: {response.status_code}")
        
        # 3. Test original API transcription
        print("\n3️⃣ Testing original /transcribe endpoint...")
        
        # Get a test file
        test_file = Path("/home/davegornshtein/parakeet-tdt-deployment/music_library/other/9afe16dd_05_Don't_You_Worry_Child.flac")
        
        if test_file.exists():
            with open(test_file, 'rb') as f:
                files = {'file': (test_file.name, f, 'audio/flac')}
                response = session.post(
                    f"{BASE_URL}/transcribe",
                    files=files
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✓ Direct transcription successful!")
                    print(f"  Processing time: {data['processing_time']:.1f}s")
                    print(f"  Text preview: {data['text'][:100]}...")
                else:
                    print(f"✗ Failed: {response.status_code}")
        
        # 4. Summary
        print("\n" + "=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"Total FLAC files: {len(flac_files)}")
        print(f"Successfully transcribed: {len(transcribed)}")
        
        if transcribed:
            print("\nTranscribed files:")
            for t in transcribed:
                has_text = "Yes" if t['text'] else "No"
                speed = t['audio_duration'] / max(t['processing_time'], 0.1)
                print(f"  - {t['filename']}: Text={has_text}, Speed={speed:.1f}x")
        
    else:
        print(f"✗ Failed to get catalog: {response.status_code}")

if __name__ == "__main__":
    test_existing_files()