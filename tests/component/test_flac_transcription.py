#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test FLAC transcription using existing API
"""
import requests
import json
import time
from pathlib import Path
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BASE_URL = "https://35.232.20.248"
USERNAME = "parakeet"
PASSWORD = "Q7+vD#8kN$2pL@9"

# Test files with known lyrics
TEST_SONGS = [
    {
        "file": "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/9afe16dd_05_Don't_You_Worry_Child.flac",
        "artist": "Swedish House Mafia",
        "title": "Don't You Worry Child",
        "expected_lyrics": ["don't you worry", "child", "heaven", "plan", "happy days"]
    },
    {
        "file": "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/3863698b_01_Pumped_up_Kicks.flac",
        "artist": "Foster The People", 
        "title": "Pumped Up Kicks",
        "expected_lyrics": ["pumped up kicks", "better run", "gun", "outrun"]
    },
    {
        "file": "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/cb3dcfc4_03_Budapest.flac",
        "artist": "George Ezra",
        "title": "Budapest",
        "expected_lyrics": ["budapest", "leave it all", "for you", "love"]
    },
    {
        "file": "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/c7963fb4_10_Wake_Me_Up.flac",
        "artist": "Avicii",
        "title": "Wake Me Up",
        "expected_lyrics": ["wake me up", "when it's all over", "wiser", "older"]
    },
    {
        "file": "/home/davegornshtein/parakeet-tdt-deployment/music_library/other/ecbb6502_04_Believe.flac",
        "artist": "Cher",
        "title": "Believe",
        "expected_lyrics": ["believe", "love", "after love", "strong enough"]
    }
]

def transcribe_music_file(file_path: str):
    """Transcribe a music file using the existing API"""
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"✗ File not found: {file_path}")
        return None
        
    print(f"\n🎵 Transcribing: {file_path.name}")
    
    # Use the existing /music/transcribe endpoint
    with requests.Session() as session:
        session.auth = (USERNAME, PASSWORD)
        session.verify = False
        
        # First, get the file path in catalog
        response = session.post(
            f"{BASE_URL}/music/transcribe",
            json={"filepath": str(file_path)}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"✗ Transcription failed: {response.status_code}")
            return None

def analyze_transcription(transcription: dict, expected_lyrics: list, song_info: dict):
    """Analyze transcription quality"""
    text = transcription.get('text', '').lower()
    
    print(f"\n📊 Analysis for: {song_info['artist']} - {song_info['title']}")
    print(f"  Duration: {transcription.get('audio_duration', 0):.1f}s")
    print(f"  Processing time: {transcription.get('processing_time', 0):.1f}s")
    print(f"  Speed: {transcription.get('audio_duration', 0)/max(transcription.get('processing_time', 1), 0.1):.1f}x realtime")
    
    if text:
        print(f"  Text length: {len(text)} characters")
        print(f"  Preview: {text[:200]}...")
        
        # Check for expected lyrics
        found_lyrics = []
        missing_lyrics = []
        
        for lyric in expected_lyrics:
            if lyric in text:
                found_lyrics.append(lyric)
            else:
                missing_lyrics.append(lyric)
        
        print(f"\n  Lyrics detection:")
        print(f"  ✓ Found ({len(found_lyrics)}/{len(expected_lyrics)}): {', '.join(found_lyrics)}")
        if missing_lyrics:
            print(f"  ✗ Missing: {', '.join(missing_lyrics)}")
        
        accuracy = (len(found_lyrics) / len(expected_lyrics)) * 100
        print(f"  Accuracy estimate: {accuracy:.0f}%")
    else:
        print(f"  ⚠️  No text detected (instrumental or recognition failed)")
    
    return text

def search_lyrics_online(artist: str, title: str):
    """Simulate lyrics search (placeholder for actual implementation)"""
    print(f"\n🔍 Searching for lyrics: {artist} - {title}")
    print("  ℹ️  Online lyrics search not implemented yet")
    print("  This would use Brave Search API or Tavily API")
    return None

def main():
    print("=" * 70)
    print("🎵 Music Transcription Test - FLAC Files")
    print("=" * 70)
    
    results = []
    
    for song in TEST_SONGS:
        file_path = song["file"]
        
        # Transcribe
        transcription = transcribe_music_file(file_path)
        
        if transcription:
            # Analyze
            text = analyze_transcription(
                transcription, 
                song["expected_lyrics"],
                {"artist": song["artist"], "title": song["title"]}
            )
            
            # Search for actual lyrics (placeholder)
            search_lyrics_online(song["artist"], song["title"])
            
            results.append({
                "song": f"{song['artist']} - {song['title']}",
                "success": True,
                "has_text": bool(text),
                "accuracy": len([l for l in song["expected_lyrics"] if l in (text or "").lower()]) / len(song["expected_lyrics"]) * 100
            })
        else:
            results.append({
                "song": f"{song['artist']} - {song['title']}",
                "success": False,
                "has_text": False,
                "accuracy": 0
            })
        
        print("\n" + "-" * 70)
        time.sleep(2)  # Delay between requests
    
    # Summary
    print("\n" + "=" * 70)
    print("📈 SUMMARY")
    print("=" * 70)
    
    successful = sum(1 for r in results if r["success"])
    with_text = sum(1 for r in results if r["has_text"])
    avg_accuracy = sum(r["accuracy"] for r in results) / len(results) if results else 0
    
    print(f"\nTotal songs tested: {len(results)}")
    print(f"Successfully processed: {successful}/{len(results)}")
    print(f"Detected vocals: {with_text}/{successful}")
    print(f"Average accuracy: {avg_accuracy:.0f}%")
    
    print("\nPer-song results:")
    for r in results:
        status = "✓" if r["success"] else "✗"
        text_status = "with text" if r["has_text"] else "no text"
        print(f"  {status} {r['song']}: {text_status} ({r['accuracy']:.0f}% accuracy)")
    
    print("\n💡 Notes:")
    print("  - Parakeet ASR is optimized for speech, not singing")
    print("  - Music with clear vocals may still be challenging")
    print("  - Background music can interfere with recognition")
    print("  - Better results expected with spoken word or podcasts")

if __name__ == "__main__":
    main()