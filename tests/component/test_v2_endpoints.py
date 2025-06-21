#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test script for Music Analyzer V2 endpoints
"""
import requests
import os
import json
from pathlib import Path

# Configuration
BASE_URL = "https://35.232.20.248"
USERNAME = "parakeet"
PASSWORD = "Q7+sKsoPWJH5vuulfY+RuQSmUyZj3jBa09Ql5om32hI="  # Use the FastAPI password

# Disable SSL warnings for self-signed certificate
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_v2_info():
    """Test V2 info endpoint"""
    print("\n1. Testing V2 Info endpoint...")
    response = requests.get(
        f"{BASE_URL}/api/v2/info",
        verify=False
    )
    
    assert response.status_code == 200, f"V2 Info failed: {response.status_code}"
    
    data = response.json()
    print(f"✓ V2 Info: {data['name']} v{data['version']}")
    print(f"  Features: {len(data['features'])} available")
    print(f"  Endpoints: {len(data['endpoints'])} available")

def test_v2_health():
    """Test V2 health endpoint"""
    print("\n2. Testing V2 Health endpoint...")
    response = requests.get(
        f"{BASE_URL}/api/v2/health",
        verify=False
    )
    
    assert response.status_code == 200, f"V2 Health failed: {response.status_code}"
    
    data = response.json()
    print(f"✓ V2 Health: {data['status']}")
    for service, status in data['services'].items():
        print(f"  - {service}: {'✓' if status else '✗'}")

def test_v2_storage_stats():
    """Test V2 storage stats endpoint"""
    print("\n3. Testing V2 Storage Stats endpoint...")
    response = requests.get(
        f"{BASE_URL}/api/v2/storage/stats",
        auth=(USERNAME, PASSWORD),
        verify=False
    )
    
    assert response.status_code == 200, f"Failed: {response.status_code}"
    
    data = response.json()
    print(f"✓ V2 Storage Stats:")
    print(f"  - Original files: {data['original_files']['count']} ({data['original_files']['total_size']} bytes)")
    print(f"  - Converted files: {data['converted_files']['count']} ({data['converted_files']['total_size']} bytes)")
    print(f"  - Cache files: {data['cache_files']['count']} ({data['cache_files']['total_size']} bytes)")
    print(f"  - Available space: {data['available_space'] / 1024**3:.1f} GB")


def test_v2_catalog():
    """Test V2 catalog endpoint"""
    print("\n4. Testing V2 Catalog endpoint...")
    response = requests.get(
        f"{BASE_URL}/api/v2/catalog",
        auth=(USERNAME, PASSWORD),
        verify=False
    )
    
    assert response.status_code == 200, f"Failed: {response.status_code}"
    
    data = response.json()
    print(f"✓ V2 Catalog:")
    print(f"  - Total files: {data['stats']['total_files']}")
    print(f"  - Total size: {data['stats']['total_size'] / 1024**2:.1f} MB")
    
    if data['stats']['by_genre']:
        print("  - By genre:")
        for genre, info in data['stats']['by_genre'].items():
            print(f"    - {genre}: {info['count']} files ({info['size'] / 1024**2:.1f} MB)")


def test_v2_file_list():
    """Test V2 file list endpoint"""
    print("\n5. Testing V2 File List endpoint...")
    response = requests.post(
        f"{BASE_URL}/api/v2/files",
        auth=(USERNAME, PASSWORD),
        json={
            "page": 1,
            "per_page": 10,
            "sort_by": "uploaded_at",
            "sort_order": "desc"
        },
        verify=False
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ V2 File List:")
        print(f"  - Files on page: {len(data['files'])}")
        print(f"  - Total files: {data['pagination']['total_count']}")
        print(f"  - Total pages: {data['pagination']['total_pages']}")
        
        if data['files']:
            print("  - Recent files:")
            for file in data['files'][:3]:
                print(f"    - {file['filename']} ({file['genre']}, {file['size'] / 1024**2:.1f} MB)")
        
    else:
        print(f"✗ V2 File List failed: {response.status_code}")
        print(f"  Response: {response.text}")
        assert False

def test_v2_upload():
    """Test V2 upload endpoint with sample file"""
    print("\n6. Testing V2 Upload endpoint...")
    
    # Check if sample file exists
    sample_file = Path("/home/davegornshtein/parakeet-tdt-deployment/test_audio/sample_speech.wav")
    if not sample_file.exists():
        print("✗ Sample file not found, skipping upload test")
        assert False
    
    with open(sample_file, 'rb') as f:
        files = {'file': (sample_file.name, f, 'audio/wav')}
        response = requests.post(
            f"{BASE_URL}/api/v2/upload",
            auth=(USERNAME, PASSWORD),
            files=files,
            verify=False
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ V2 Upload successful:")
        print(f"  - File ID: {data['file_id']}")
        print(f"  - Genre: {data['genre']}")
        print(f"  - Duration: {data['duration']:.2f}s")
        print(f"  - Hash: {data['hash'][:8]}...")
    elif response.status_code == 400 and "already exists" in response.text:
        print("✓ V2 Upload: File already exists (expected)")
    else:
        print(f"✗ V2 Upload failed: {response.status_code}")
        print(f"  Response: {response.text}")
        assert False

def main():
    """Run all V2 endpoint tests"""
    print("Music Analyzer V2 Endpoints Test")
    print("=" * 50)
    
    # Track results
    results = []
    
    # Run tests
    results.append(("V2 Info", test_v2_info()))
    results.append(("V2 Health", test_v2_health()))
    results.append(("V2 Storage Stats", test_v2_storage_stats()))
    results.append(("V2 Catalog", test_v2_catalog()))
    results.append(("V2 File List", test_v2_file_list()))
    results.append(("V2 Upload", test_v2_upload()))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        print(f"  - {test_name}: {'✓ PASSED' if result else '✗ FAILED'}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All V2 endpoints are working correctly!")
    else:
        print(f"\n✗ {total - passed} tests failed")

if __name__ == "__main__":
    main()