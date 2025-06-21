#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test direct transcription of FLAC files
"""
import requests
import os
from pathlib import Path
import urllib3
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.test")

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BASE_URL = os.getenv("TEST_API_URL", "https://35.232.20.248")
USERNAME = os.getenv("API_USERNAME", "parakeet")
PASSWORD = os.getenv("API_PASSWORD", "Q7+vD#8kN$2pL@9")

# Test one FLAC file
test_file = "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/9afe16dd_05_Don't_You_Worry_Child.flac"

print(f"Testing direct transcription of: {Path(test_file).name}")
print(f"File size: {os.path.getsize(test_file) / 1024**2:.1f} MB")

# Upload and transcribe
with open(test_file, 'rb') as f:
    files = {'file': (Path(test_file).name, f, 'audio/flac')}
    
    response = requests.post(
        f"{BASE_URL}/transcribe",
        auth=(USERNAME, PASSWORD),
        files=files,
        verify=False
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Transcription successful!")
        print(f"  - Language: {data.get('language', 'unknown')}")
        print(f"  - Processing time: {data.get('processing_time', 0):.2f}s")
        print(f"  - Audio duration: {data.get('audio_duration', 0):.2f}s")
        print(f"  - Text length: {len(data.get('text', ''))} characters")
        
        text = data.get('text', '')
        if text:
            print(f"\nTranscription preview:")
            print(f"{text[:500]}...")
        else:
            print("\nNo text detected (possibly instrumental)")
    else:
        print(f"✗ Failed: {response.text[:200]}")