#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""Test script for Parakeet TDT API"""

import requests
import json
import time

API_URL = "http://localhost:8000"

def test_health():
    print("1. Testing health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_gpu_stats():
    print("2. Testing GPU stats endpoint...")
    response = requests.get(f"{API_URL}/gpu/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_synthesis():
    print("3. Testing TTS synthesis...")
    
    texts = [
        "Hello world!",
        "This is a test of the NVIDIA Parakeet text to speech system.",
        "The quick brown fox jumps over the lazy dog.",
    ]
    
    for i, text in enumerate(texts):
        print(f"\nSynthesizing: '{text}'")
        
        payload = {"text": text}
        start_time = time.time()
        
        response = requests.post(
            f"{API_URL}/synthesize",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        end_time = time.time()
        
        if response.status_code == 200:
            # Save audio file
            filename = f"test_output_{i+1}.wav"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ Success! Audio saved to {filename}")
            print(f"  Processing time: {end_time - start_time:.2f}s")
            print(f"  File size: {len(response.content) / 1024:.1f} KB")
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  Response: {response.text}")

def test_different_parameters():
    print("\n4. Testing with different parameters...")
    
    payload = {
        "text": "Testing different speech speeds and sample rates.",
        "speed": 1.2,  # Faster speech
        "sample_rate": 44100  # Higher sample rate
    }
    
    response = requests.post(f"{API_URL}/synthesize", json=payload)
    
    if response.status_code == 200:
        with open("test_output_custom.wav", 'wb') as f:
            f.write(response.content)
        print(f"✓ Custom parameters test successful!")
    else:
        print(f"✗ Error: {response.text}")

if __name__ == "__main__":
    print("=== Parakeet TDT API Test Suite ===\n")
    
    try:
        test_health()
        test_gpu_stats()
        test_synthesis()
        test_different_parameters()
        
        print("\n=== All tests completed! ===")
        print("\nAudio files generated:")
        import os
        for f in os.listdir('.'):
            if f.startswith('test_output') and f.endswith('.wav'):
                size = os.path.getsize(f) / 1024
                print(f"  - {f} ({size:.1f} KB)")
                
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to API server. Is it running?")
    except Exception as e:
        print(f"ERROR: {str(e)}")