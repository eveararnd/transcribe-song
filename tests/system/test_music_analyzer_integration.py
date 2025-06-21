#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Comprehensive integration test for Music Analyzer V2
Tests the complete workflow: upload, transcribe, search, lyrics
"""
import asyncio
import requests
import json
import time
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.test")

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Configuration
BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")  # Main Parakeet API with V2 endpoints
USERNAME = os.getenv("API_USERNAME", "parakeet")
PASSWORD = os.getenv("API_PASSWORD", "Q7+sKsoPWJH5vuulfY+RuQSmUyZj3jBa09Ql5om32hI=")

class MusicAnalyzerTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.auth = (USERNAME, PASSWORD)
        self.uploaded_files = []
    
    def test_api_info(self):
        """Test API info endpoint"""
        print("\n1️⃣ Testing API Info...")
        response = self.session.get(f"{BASE_URL}/api/v2/info")
        
        if response.status_code == 200:
            info = response.json()
            print(f"✓ API Name: {info['name']}")
            print(f"✓ Version: {info['version']}")
            print(f"✓ Features: {', '.join(info['features'])}")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
    
    def test_upload_flac(self):
        """Test uploading FLAC files"""
        print("\n2️⃣ Testing File Upload...")
        
        # Get first available FLAC file
        flac_dir = Path("/home/davegornshtein/parakeet-tdt-deployment/music_library/other")
        flac_files = list(flac_dir.glob("*.flac"))[:3]  # Test with 3 files
        
        if not flac_files:
            print("✗ No FLAC files found")
            return False
        
        for flac_file in flac_files:
            print(f"\nUploading: {flac_file.name}")
            
            with open(flac_file, 'rb') as f:
                files = {'file': (flac_file.name, f, 'audio/flac')}
                response = self.session.post(
                    f"{BASE_URL}/api/v2/upload",
                    files=files
                )
            
            if response.status_code == 200:
                data = response.json()
                self.uploaded_files.append(data)
                print(f"✓ Uploaded: {data['filename']}")
                print(f"  File ID: {data['file_id']}")
                print(f"  Genre: {data['genre']}")
                print(f"  Duration: {data['duration']:.1f}s")
            else:
                print(f"✗ Upload failed: {response.status_code}")
                if response.status_code == 400:
                    print(f"  (File may already exist)")
        
        return len(self.uploaded_files) > 0
    
    def test_catalog(self):
        """Test catalog endpoint"""
        print("\n3️⃣ Testing Catalog...")
        response = self.session.get(f"{BASE_URL}/api/v2/catalog")
        
        if response.status_code == 200:
            catalog = response.json()
            stats = catalog['stats']
            print(f"✓ Total files: {stats['total_files']}")
            print(f"✓ Total size: {stats['total_size'] / 1024**2:.1f} MB")
            print(f"✓ Genres: {', '.join(stats['by_genre'].keys())}")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
    
    def test_transcription(self):
        """Test transcription of uploaded files"""
        print("\n4️⃣ Testing Transcription...")
        
        if not self.uploaded_files:
            print("✗ No files to transcribe")
            return False
        
        transcribed = []
        
        for file_info in self.uploaded_files[:2]:  # Transcribe first 2 files
            print(f"\nTranscribing: {file_info['filename']}")
            
            response = self.session.post(
                f"{BASE_URL}/api/v2/transcribe",
                json={"file_id": file_info['file_id']}
            )
            
            if response.status_code == 200:
                data = response.json()
                transcribed.append(data)
                print(f"✓ Transcribed in {data['processing_time']:.1f}s")
                print(f"  Speed: {data['audio_duration']/data['processing_time']:.1f}x realtime")
                if data['text']:
                    print(f"  Text preview: {data['text'][:100]}...")
                else:
                    print(f"  No text detected (instrumental?)")
            else:
                print(f"✗ Transcription failed: {response.status_code}")
        
        return len(transcribed) > 0
    
    def test_vector_search(self):
        """Test FAISS vector search"""
        print("\n5️⃣ Testing Vector Search...")
        
        test_queries = [
            "pumped up kicks",
            "worry child heaven",
            "lazy song"
        ]
        
        for query in test_queries:
            print(f"\nSearching: '{query}'")
            
            response = self.session.post(
                f"{BASE_URL}/api/v2/search/vector",
                json={"query": query, "k": 3}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Found {data['total']} results")
                for i, result in enumerate(data['results'][:3], 1):
                    print(f"  {i}. {result['filename']} (score: {result['score']:.3f})")
            else:
                print(f"✗ Search failed: {response.status_code}")
        
        return True
    
    def test_similar_songs(self):
        """Test finding similar songs"""
        print("\n6️⃣ Testing Similar Songs...")
        
        if not self.uploaded_files:
            print("✗ No files to test")
            return False
        
        file_id = self.uploaded_files[0]['file_id']
        filename = self.uploaded_files[0]['filename']
        
        print(f"Finding songs similar to: {filename}")
        
        response = self.session.post(
            f"{BASE_URL}/api/v2/search/similar",
            json={"file_id": file_id, "k": 5}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data['total']} similar songs")
            for i, song in enumerate(data['similar_songs'][:3], 1):
                print(f"  {i}. {song['filename']} (score: {song['score']:.3f})")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
    
    def test_lyrics_search(self):
        """Test lyrics search"""
        print("\n7️⃣ Testing Lyrics Search...")
        
        if not self.uploaded_files:
            print("✗ No files to test")
            return False
        
        # Test with first uploaded file
        file_info = self.uploaded_files[0]
        
        print(f"Searching lyrics for: {file_info['filename']}")
        
        response = self.session.post(
            f"{BASE_URL}/api/v2/search/lyrics",
            json={"file_id": file_info['file_id'], "source": "tavily"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Artist: {data['artist']}")
            print(f"✓ Title: {data['title']}")
            
            results = data['search_results'].get('results', {})
            if results:
                print(f"✓ Found lyrics from {len(results)} source(s)")
                if 'tavily' in results and results['tavily'].get('lyrics'):
                    print(f"  Lyrics preview: {results['tavily']['lyrics'][:100]}...")
            else:
                print("✗ No lyrics found")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
    
    def test_search_stats(self):
        """Test FAISS statistics"""
        print("\n8️⃣ Testing Search Statistics...")
        
        response = self.session.get(f"{BASE_URL}/api/v2/search/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✓ Total vectors: {stats['total_vectors']}")
            print(f"✓ Embedding dimension: {stats['embedding_dimension']}")
            print(f"✓ Index size: {stats['index_size_mb']:.2f} MB")
            print(f"✓ Unique files: {stats['unique_files']}")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 70)
        print("🎵 MUSIC ANALYZER V2 - INTEGRATION TEST")
        print("=" * 70)
        
        tests = [
            ("API Info", self.test_api_info),
            ("File Upload", self.test_upload_flac),
            ("Catalog", self.test_catalog),
            ("Transcription", self.test_transcription),
            ("Vector Search", self.test_vector_search),
            ("Similar Songs", self.test_similar_songs),
            ("Lyrics Search", self.test_lyrics_search),
            ("Search Stats", self.test_search_stats)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"✗ {test_name} error: {e}")
                failed += 1
        
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"✓ Passed: {passed}/{len(tests)}")
        print(f"✗ Failed: {failed}/{len(tests)}")
        
        if failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")
        
        return failed == 0

def main():
    """Main test runner"""
    tester = MusicAnalyzerTester()
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/api/v2/info", timeout=2)
        if response.status_code != 200:
            print("⚠️  Music Analyzer API is not responding properly")
            print("Please ensure the API is running on port 8001")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to Music Analyzer API")
        print("Please start the API with:")
        print("  source /home/davegornshtein/parakeet-env/bin/activate")
        print("  python music_analyzer_api.py")
        return
    
    # Run tests
    tester.run_all_tests()

if __name__ == "__main__":
    main()