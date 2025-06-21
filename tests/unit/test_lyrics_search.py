#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test lyrics search functionality
"""
import asyncio
from src.managers.lyrics_search_manager import LyricsSearchManager
import json

async def test_lyrics_search():
    """Test lyrics search with real songs"""
    print("🎵 Testing Lyrics Search Integration")
    print("=" * 70)
    
    # Initialize lyrics manager
    lyrics_manager = LyricsSearchManager()
    
    # Test songs
    test_songs = [
        {"artist": "Foster The People", "title": "Pumped Up Kicks"},
        {"artist": "Swedish House Mafia", "title": "Don't You Worry Child"},
        {"artist": "Bruno Mars", "title": "The Lazy Song"},
        {"artist": "Sting", "title": "Englishman in New York"},
    ]
    
    # Test both Brave and Tavily
    for song in test_songs:
        print(f"\n🔍 Searching: {song['artist']} - {song['title']}")
        print("-" * 50)
        
        # Search with both APIs
        results = await lyrics_manager.search_lyrics(
            artist=song['artist'],
            title=song['title'],
            source="both"
        )
        
        # Display results
        if results.get("results"):
            print(f"✓ Found lyrics from {len(results['results'])} source(s)")
            
            # Show Brave results
            if "brave" in results["results"]:
                brave = results["results"]["brave"]
                print(f"\n  Brave Search:")
                print(f"    Site: {brave.get('site', 'Unknown')}")
                print(f"    Confidence: {brave.get('confidence', 0):.2f}")
                print(f"    URL: {brave.get('url', 'N/A')[:70]}...")
                print(f"    Snippet: {brave.get('snippet', '')[:100]}...")
            
            # Show Tavily results
            if "tavily" in results["results"]:
                tavily = results["results"]["tavily"]
                print(f"\n  Tavily Search:")
                if tavily.get("lyrics"):
                    print(f"    ✓ Found direct lyrics ({len(tavily['lyrics'])} chars)")
                    print(f"    Preview: {tavily['lyrics'][:150]}...")
                else:
                    print(f"    Site: {tavily.get('site', 'Unknown')}")
                    print(f"    Confidence: {tavily.get('confidence', 0):.2f}")
                    print(f"    URL: {tavily.get('url', 'N/A')[:70]}...")
                    if tavily.get("full_content"):
                        print(f"    Content length: {len(tavily['full_content'])} chars")
            
            # Best source
            if results.get("best_source"):
                print(f"\n  📌 Best source: {results['best_source']}")
        else:
            print("✗ No lyrics found")
    
    # Test edge cases
    print("\n\n🧪 Testing Edge Cases")
    print("=" * 70)
    
    # Test with non-existent song
    print("\n1. Non-existent song:")
    results = await lyrics_manager.search_lyrics(
        artist="Fake Artist",
        title="Non Existent Song XYZ123",
        source="both"
    )
    print(f"   Results found: {len(results.get('results', {}))}")
    
    # Test with only Brave
    print("\n2. Brave-only search:")
    results = await lyrics_manager.search_lyrics(
        artist="The Beatles",
        title="Hey Jude",
        source="brave"
    )
    print(f"   Brave results: {'Yes' if 'brave' in results.get('results', {}) else 'No'}")
    print(f"   Tavily results: {'Yes' if 'tavily' in results.get('results', {}) else 'No'}")
    
    # Test with only Tavily
    print("\n3. Tavily-only search:")
    results = await lyrics_manager.search_lyrics(
        artist="Queen",
        title="Bohemian Rhapsody",
        source="tavily"
    )
    print(f"   Brave results: {'Yes' if 'brave' in results.get('results', {}) else 'No'}")
    print(f"   Tavily results: {'Yes' if 'tavily' in results.get('results', {}) else 'No'}")
    
    print("\n✓ Lyrics search tests completed!")

if __name__ == "__main__":
    asyncio.run(test_lyrics_search())