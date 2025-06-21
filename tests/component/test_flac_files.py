#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test Music Analyzer V2 with FLAC files
"""
import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import urllib3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.test")

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BASE_URL = os.getenv("TEST_API_URL", "https://35.232.20.248")
USERNAME = os.getenv("API_USERNAME", "parakeet")
PASSWORD = os.getenv("API_PASSWORD", "Q7+vD#8kN$2pL@9")  # nginx password

# Test files
TEST_FILES = [
    "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/9afe16dd_05_Don't_You_Worry_Child.flac",
    "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/3863698b_01_Pumped_up_Kicks.flac",
    "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/cb3dcfc4_03_Budapest.flac",
    "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/c7963fb4_10_Wake_Me_Up.flac",
    "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/ecbb6502_04_Believe.flac"
]

class MusicAnalyzerV2Tester:
    def __init__(self):
        self.session = requests.Session()
        self.session.auth = (USERNAME, PASSWORD)
        self.session.verify = False
        self.uploaded_files = []
        
    def test_health(self):
        """Test V2 health endpoint"""
        print("\n🔍 Testing V2 Health...")
        response = self.session.get(f"{BASE_URL}/api/v2/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health Status: {data['status']}")
            for service, status in data['services'].items():
                print(f"  - {service}: {'✓' if status else '✗'}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    
    def upload_flac_file(self, file_path: str) -> Optional[str]:
        """Upload a FLAC file to V2 API"""
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"✗ File not found: {file_path}")
            return None
            
        print(f"\n📤 Uploading: {file_path.name}")
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'audio/flac')}
            response = self.session.post(
                f"{BASE_URL}/api/v2/upload",
                files=files
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Upload successful!")
            print(f"  - File ID: {data['file_id']}")
            print(f"  - Genre: {data['genre']}")
            print(f"  - Duration: {data.get('duration', 0):.2f}s")
            print(f"  - Size: {data['size'] / 1024**2:.1f} MB")
            self.uploaded_files.append(data)
            return data['file_id']
        elif response.status_code == 400 and "already exists" in response.text:
            # Extract file ID from existing file
            print("ℹ️  File already exists, getting info from catalog...")
            return self.find_file_in_catalog(file_path.name)
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None
    
    def find_file_in_catalog(self, filename: str) -> Optional[str]:
        """Find file ID in catalog by filename"""
        response = self.session.get(f"{BASE_URL}/api/v2/catalog")
        if response.status_code == 200:
            catalog = response.json()
            for file_id, file_info in catalog.get('files', {}).items():
                if filename in file_info.get('filename', ''):
                    print(f"  - Found existing file ID: {file_id}")
                    return file_id
        return None
    
    def transcribe_file(self, file_id: str) -> Optional[Dict]:
        """Transcribe a file using V2 API"""
        print(f"\n🎵 Transcribing file: {file_id}")
        
        response = self.session.post(
            f"{BASE_URL}/api/v2/transcribe",
            json={
                "file_id": file_id,
                "timestamps": False,
                "return_segments": False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Transcription successful!")
            print(f"  - Processing time: {data['processing_time']:.2f}s")
            print(f"  - Audio duration: {data['audio_duration']:.2f}s")
            print(f"  - Text length: {len(data['text'])} characters")
            if data['text']:
                print(f"  - Preview: {data['text'][:100]}...")
            else:
                print(f"  - Text: (empty - likely instrumental)")
            return data
        else:
            print(f"✗ Transcription failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None
    
    def test_catalog(self):
        """Test V2 catalog endpoint"""
        print("\n📚 Testing V2 Catalog...")
        response = self.session.get(f"{BASE_URL}/api/v2/catalog")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Catalog retrieved successfully!")
            print(f"  - Total files: {data['stats']['total_files']}")
            print(f"  - Total size: {data['stats']['total_size'] / 1024**3:.2f} GB")
            
            if data['stats'].get('by_genre'):
                print("  - By genre:")
                for genre, info in data['stats']['by_genre'].items():
                    print(f"    - {genre}: {info['count']} files ({info['size'] / 1024**2:.1f} MB)")
                    
            if data['stats'].get('by_format'):
                print("  - By format:")
                for fmt, info in data['stats']['by_format'].items():
                    print(f"    - {fmt}: {info['count']} files")
            
            return True
        else:
            print(f"✗ Catalog failed: {response.status_code}")
            return False
    
    def test_storage_stats(self):
        """Test V2 storage statistics"""
        print("\n💾 Testing V2 Storage Stats...")
        response = self.session.get(f"{BASE_URL}/api/v2/storage/stats")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Storage stats retrieved!")
            print(f"  - Original files: {data['original_files']['count']} ({data['original_files']['total_size'] / 1024**2:.1f} MB)")
            print(f"  - Converted files: {data['converted_files']['count']} ({data['converted_files']['total_size'] / 1024**2:.1f} MB)")
            print(f"  - Database entries: {data.get('database_entries', 0)}")
            print(f"  - Available space: {data['available_space'] / 1024**3:.1f} GB")
            return True
        else:
            print(f"✗ Storage stats failed: {response.status_code}")
            return False
    
    def test_file_list(self):
        """Test V2 file list with search"""
        print("\n🔍 Testing V2 File List...")
        
        # Test basic listing
        response = self.session.post(
            f"{BASE_URL}/api/v2/files",
            json={
                "page": 1,
                "per_page": 5,
                "sort_by": "uploaded_at",
                "sort_order": "desc"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ File list retrieved!")
            print(f"  - Files on page: {len(data['files'])}")
            print(f"  - Total files: {data['pagination']['total_count']}")
            
            if data['files']:
                print("  - Recent files:")
                for file in data['files'][:3]:
                    print(f"    - {file['filename']} ({file.get('duration', 0):.1f}s, {file['size'] / 1024**2:.1f} MB)")
            
            # Test search
            print("\n  Testing search functionality...")
            search_response = self.session.post(
                f"{BASE_URL}/api/v2/files",
                json={
                    "page": 1,
                    "per_page": 10,
                    "search_query": "Don't You Worry"
                }
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                print(f"  ✓ Search results: {len(search_data['files'])} files found")
                for file in search_data['files']:
                    print(f"    - {file['filename']}")
            
            return True
        else:
            print(f"✗ File list failed: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all tests with FLAC files"""
        print("=" * 60)
        print("Music Analyzer V2 - FLAC Files Test Suite")
        print("=" * 60)
        
        # 1. Test health
        self.test_health()
        
        # 2. Test storage stats
        self.test_storage_stats()
        
        # 3. Upload and transcribe FLAC files
        print("\n" + "=" * 60)
        print("📁 Testing FLAC File Upload and Transcription")
        print("=" * 60)
        
        transcription_results = []
        
        for file_path in TEST_FILES[:3]:  # Test first 3 files
            file_id = self.upload_flac_file(file_path)
            if file_id:
                time.sleep(2)  # Small delay between operations
                result = self.transcribe_file(file_id)
                if result:
                    transcription_results.append({
                        'file': Path(file_path).name,
                        'file_id': file_id,
                        'text': result['text'],
                        'duration': result['audio_duration'],
                        'processing_time': result['processing_time']
                    })
        
        # 4. Test catalog
        self.test_catalog()
        
        # 5. Test file list
        self.test_file_list()
        
        # 6. Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        print(f"\nTranscription Results:")
        for i, result in enumerate(transcription_results, 1):
            print(f"\n{i}. {result['file']}")
            print(f"   - Duration: {result['duration']:.1f}s")
            print(f"   - Processing: {result['processing_time']:.1f}s")
            print(f"   - Speed: {result['duration']/result['processing_time']:.1f}x realtime")
            if result['text']:
                print(f"   - Text: {result['text'][:150]}...")
            else:
                print(f"   - Text: (empty - instrumental or no vocals detected)")
        
        print("\n✅ All tests completed!")

if __name__ == "__main__":
    tester = MusicAnalyzerV2Tester()
    tester.run_all_tests()