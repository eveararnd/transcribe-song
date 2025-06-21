#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test Gemma integration with Music Analyzer
"""
import asyncio
import time
from src.models.gemma_manager import GemmaManager
from src.utils.lyrics_search_enhanced import EnhancedLyricsSearchManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_gemma_lyrics_analysis():
    """Test Gemma model for lyrics analysis"""
    print("🤖 Testing Gemma Integration")
    print("=" * 70)
    
    # Initialize Gemma manager
    print("\n1️⃣ Initializing Gemma model...")
    gemma = GemmaManager()
    
    try:
        await asyncio.to_thread(gemma.load_model)
        print("✓ Gemma model loaded successfully")
        
        model_info = gemma.get_model_info()
        print(f"  Model: {model_info['model_name']}")
        print(f"  Device: {model_info['device']}")
        print(f"  Parameters: {model_info['parameters']:,}")
        if model_info['device'] == 'cuda':
            print(f"  GPU Memory: {model_info['memory_usage_mb']:.1f} MB")
    except Exception as e:
        print(f"✗ Failed to load Gemma: {e}")
        return
    
    # Test lyrics analysis
    print("\n2️⃣ Testing lyrics analysis...")
    
    test_lyrics = [
        {
            "text": "don't you worry child see heaven's got a plan for you",
            "expected_mood": "hopeful/reassuring"
        },
        {
            "text": "pumped up kicks better run better run outrun my gun",
            "expected_mood": "dark/threatening"
        },
        {
            "text": "lazy song today i don't feel like doing anything i just wanna lay in my bed",
            "expected_mood": "relaxed/carefree"
        }
    ]
    
    for lyrics_data in test_lyrics:
        print(f"\n  Analyzing: '{lyrics_data['text'][:50]}...'")
        
        # Summary
        summary_result = await gemma.analyze_lyrics(lyrics_data['text'], "summary")
        print(f"  Summary: {summary_result['analysis'][:100]}...")
        
        # Mood
        mood_result = await gemma.analyze_lyrics(lyrics_data['text'], "mood")
        print(f"  Mood: {mood_result['analysis'][:100]}...")
        print(f"  Processing time: {mood_result['processing_time']:.2f}s")
    
    # Test transcription comparison
    print("\n3️⃣ Testing transcription comparison...")
    
    transcribed = "don't worry child see heaven got a plan for you"
    actual = "Don't you worry child, see heaven's got a plan for you"
    
    comparison = await gemma.compare_transcriptions(transcribed, actual)
    print(f"  Comparison result: {comparison['comparison'][:200]}...")
    
    # Test intelligent lyrics search
    print("\n4️⃣ Testing intelligent lyrics search...")
    
    enhanced_manager = EnhancedLyricsSearchManager()
    await enhanced_manager.initialize_gemma()
    
    if enhanced_manager.gemma_loaded:
        print("✓ Gemma loaded for enhanced lyrics search")
        
        # Test search with Gemma decision making
        results = await enhanced_manager.search_lyrics_intelligent(
            artist="Swedish House Mafia",
            title="Don't You Worry Child",
            transcribed_text="don't worry child see heaven got a plan for you"
        )
        
        print(f"\n  Search strategy: {results.get('search_strategy')}")
        print(f"  Sources searched: {list(results.get('results', {}).keys())}")
        print(f"  Best source: {results.get('best_source')}")
        
        if results.get('analysis'):
            if 'brave_quality' in results['analysis']:
                print(f"  Brave quality score: {results['analysis']['brave_quality'].get('score', 'N/A')}/10")
            if 'need_tavily' in results['analysis']:
                print(f"  Need Tavily search: {results['analysis']['need_tavily']}")
            if 'tavily_quality' in results['analysis']:
                print(f"  Tavily quality score: {results['analysis']['tavily_quality'].get('score', 'N/A')}/10")
    else:
        print("✗ Failed to load Gemma for enhanced search")
    
    # Test song insights
    print("\n5️⃣ Testing song insights generation...")
    
    metadata = {
        "title": "Don't You Worry Child",
        "artist": "Swedish House Mafia",
        "genre": "electronic"
    }
    
    insights = await gemma.generate_song_insights(
        "don't you worry child see heaven's got a plan for you",
        metadata
    )
    
    print(f"  Insights: {insights['insights'][:300]}...")
    print(f"  Processing time: {insights['processing_time']:.2f}s")
    
    print("\n✓ All Gemma tests completed!")

async def test_gemma_performance():
    """Test Gemma performance with multiple requests"""
    print("\n" + "=" * 70)
    print("📊 Testing Gemma Performance")
    print("=" * 70)
    
    gemma = GemmaManager()
    
    # Skip if model not loaded
    if gemma.model is None:
        try:
            await asyncio.to_thread(gemma.load_model)
        except:
            print("✗ Cannot test performance - model not loaded")
            return
    
    # Test different text lengths
    test_texts = [
        "short text for quick analysis",
        "medium length text that contains more content for analysis including various themes and emotions " * 3,
        "long text for comprehensive analysis " * 20
    ]
    
    print("\nResponse times by text length:")
    
    for i, text in enumerate(test_texts):
        start = time.time()
        result = await gemma.analyze_lyrics(text, "all")
        elapsed = time.time() - start
        
        print(f"  {['Short', 'Medium', 'Long'][i]} ({len(text)} chars): {elapsed:.2f}s")
    
    # Test concurrent requests
    print("\nConcurrent request handling (3 simultaneous):")
    
    start = time.time()
    tasks = [
        gemma.analyze_lyrics("test lyrics 1", "summary"),
        gemma.analyze_lyrics("test lyrics 2", "mood"),
        gemma.analyze_lyrics("test lyrics 3", "theme")
    ]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    print(f"  Total time for 3 concurrent requests: {elapsed:.2f}s")
    print(f"  Average time per request: {elapsed/3:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_gemma_lyrics_analysis())
    asyncio.run(test_gemma_performance())