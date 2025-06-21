#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test API locally without nginx
"""
import requests
import urllib3
from pathlib import Path

# Disable SSL warnings
urllib3.disable_warnings()

# Test files
test_files = [
    "/home/davegornshtein/parakeet-tdt-deployment/test_audio/sample_speech.wav",
    "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/9afe16dd_05_Don't_You_Worry_Child.flac"
]

# Direct API endpoint
API_URL = "http://localhost:8000"
USERNAME = "parakeet"
PASSWORD = "Q7+sKsoPWJH5vuulfY+RuQSmUyZj3jBa09Ql5om32hI="

print("Testing API directly on localhost:8000\n")

# Test health endpoint
print("1. Testing health endpoint...")
response = requests.get(f"{API_URL}/health")
if response.status_code == 200:
    data = response.json()
    print(f"✓ Health check passed: {data['status']}")
    print(f"  Model loaded: {data.get('model_loaded', False)}")
    print(f"  CUDA available: {data.get('cuda_available', False)}")
else:
    print(f"✗ Health check failed: {response.status_code}")

# Test transcription
for test_file in test_files:
    if not Path(test_file).exists():
        continue
        
    print(f"\n2. Testing transcription of: {Path(test_file).name}")
    print(f"   File size: {Path(test_file).stat().st_size / 1024**2:.1f} MB")
    
    with open(test_file, 'rb') as f:
        files = {'file': (Path(test_file).name, f, 'audio/wav' if test_file.endswith('.wav') else 'audio/flac')}
        
        response = requests.post(
            f"{API_URL}/transcribe",
            auth=(USERNAME, PASSWORD),
            files=files
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Success!")
            print(f"   - Processing time: {data.get('processing_time', 0):.2f}s")
            print(f"   - Audio duration: {data.get('audio_duration', 0):.2f}s")
            print(f"   - Text: {data.get('text', '')[:100]}...")
        else:
            print(f"   ✗ Failed: {response.text[:100]}")

# Test V2 endpoints
print("\n3. Testing V2 endpoints...")
response = requests.get(f"{API_URL}/api/v2/info")
if response.status_code == 200:
    data = response.json()
    print(f"✓ V2 Info: {data['name']} v{data['version']}")
else:
    print(f"✗ V2 Info failed: {response.status_code}")