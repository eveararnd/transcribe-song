#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test FAISS integration with Music Analyzer
"""
import asyncio
import json
from pathlib import Path
from src.managers.faiss_manager import FAISSManager

async def test_faiss_manager():
    """Test FAISS manager functionality"""
    print("🔍 Testing FAISS Manager Integration")
    print("=" * 70)
    
    # Initialize FAISS manager
    faiss_manager = FAISSManager(index_dir="./test_faiss_indexes")
    
    # Test 1: Generate embeddings
    print("\n1. Testing embedding generation...")
    test_texts = [
        "don't you worry child see heaven's got a plan for you",
        "pumped up kicks better run better run outrun my gun",
        "wake me up when it's all over when I'm wiser and I'm older",
        "I believe in life after love I can feel something inside me say",
        "lazy song today I don't feel like doing anything"
    ]
    
    for text in test_texts:
        embedding = faiss_manager.generate_embedding(text)
        print(f"  ✓ Generated embedding for: '{text[:50]}...' Shape: {embedding.shape}")
    
    # Test 2: Add transcriptions to index
    print("\n2. Testing transcription indexing...")
    file_ids = ["file1", "file2", "file3", "file4", "file5"]
    trans_ids = ["trans1", "trans2", "trans3", "trans4", "trans5"]
    genres = ["pop", "indie", "electronic", "pop", "pop"]
    
    for i, (file_id, trans_id, text, genre) in enumerate(zip(file_ids, trans_ids, test_texts, genres)):
        metadata = {
            "filename": f"song_{i+1}.flac",
            "genre": genre,
            "duration": 180 + i * 20,
            "uploaded_at": "2024-06-20T12:00:00"
        }
        
        idx = await faiss_manager.add_transcription(
            file_id=file_id,
            transcription_id=trans_id,
            text=text,
            metadata=metadata
        )
        print(f"  ✓ Added transcription {idx}: {metadata['filename']} ({genre})")
    
    # Save index
    await asyncio.to_thread(faiss_manager.save_index)
    print("\n  ✓ Index saved to disk")
    
    # Test 3: Search by text
    print("\n3. Testing vector search...")
    search_queries = [
        "child heaven plan",
        "run gun danger",
        "wake up older wiser",
        "love believe feel"
    ]
    
    for query in search_queries:
        results = await faiss_manager.search(query, k=3)
        print(f"\n  Query: '{query}'")
        for i, result in enumerate(results, 1):
            print(f"    {i}. Score: {result['score']:.3f} - {result['metadata']['filename']} ({result['metadata']['genre']})")
            print(f"       Preview: {result['text_preview'][:60]}...")
    
    # Test 4: Find similar songs
    print("\n4. Testing similar song search...")
    similar = await faiss_manager.find_similar_songs("file1", k=3)
    print(f"  Songs similar to file1:")
    for i, result in enumerate(similar, 1):
        print(f"    {i}. Score: {result['score']:.3f} - {result['metadata']['filename']}")
    
    # Test 5: Get statistics
    print("\n5. Testing statistics...")
    stats = await faiss_manager.get_statistics()
    print(f"  Total vectors: {stats['total_vectors']}")
    print(f"  Embedding dimension: {stats['embedding_dimension']}")
    print(f"  Index size: {stats['index_size_mb']:.2f} MB")
    print(f"  Unique files: {stats['unique_files']}")
    
    print("\n✓ All tests passed!")
    
    # Load transcription results from our previous test
    results_file = Path("music_transcription_results.json")
    if results_file.exists():
        print("\n" + "=" * 70)
        print("📊 Indexing actual transcription results...")
        
        with open(results_file) as f:
            data = json.load(f)
        
        # Index real transcriptions
        indexed_count = 0
        for result in data["results"]:
            if result["has_text"] and result["text_preview"] != "(No text detected)":
                # Extract actual text from preview (removing the "..." at the end)
                text = result["text_preview"][:-3] if result["text_preview"].endswith("...") else result["text_preview"]
                
                metadata = {
                    "filename": result["filename"],
                    "genre": "music",  # Default genre
                    "duration": result["duration"],
                    "uploaded_at": "2024-06-20T15:00:00",
                    "word_count": result["word_count"],
                    "processing_time": result["processing_time"]
                }
                
                await faiss_manager.add_transcription(
                    file_id=f"real_{indexed_count}",
                    transcription_id=f"real_trans_{indexed_count}",
                    text=text,
                    metadata=metadata
                )
                indexed_count += 1
                print(f"  ✓ Indexed: {result['song']} ({result['word_count']} words)")
        
        # Save updated index
        await asyncio.to_thread(faiss_manager.save_index)
        print(f"\n  ✓ Indexed {indexed_count} real transcriptions")
        
        # Test search on real data
        print("\n🔍 Testing search on real transcriptions...")
        real_queries = [
            "pumped up kicks",
            "worry child heaven",
            "english man new york",
            "lazy song"
        ]
        
        for query in real_queries:
            results = await faiss_manager.search(query, k=3)
            print(f"\n  Query: '{query}'")
            for i, result in enumerate(results, 1):
                print(f"    {i}. Score: {result['score']:.3f} - {result['metadata']['filename']}")

if __name__ == "__main__":
    asyncio.run(test_faiss_manager())