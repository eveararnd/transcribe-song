# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Enhanced Lyrics Search Manager with Gemma Intelligence
"""
import os
import asyncio
import aiohttp
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import quote
import json
from datetime import datetime
from dotenv import load_dotenv
from src.models.gemma_manager import get_gemma_manager

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EnhancedLyricsSearchManager:
    def __init__(self):
        """Initialize enhanced lyrics search manager with Gemma integration"""
        self.brave_api_key = os.getenv('BRAVE_SEARCH_API_KEY')
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        
        # API endpoints
        self.brave_url = "https://api.search.brave.com/res/v1/web/search"
        self.tavily_url = "https://api.tavily.com/search"
        
        # Headers
        self.brave_headers = {
            "X-Subscription-Token": self.brave_api_key,
            "Accept": "application/json"
        }
        
        self.tavily_headers = {
            "Content-Type": "application/json"
        }
        
        # Initialize Gemma manager
        self.gemma_manager = get_gemma_manager()
        self.gemma_loaded = False
    
    async def initialize_gemma(self):
        """Initialize Gemma model if not already loaded"""
        if not self.gemma_loaded:
            try:
                await asyncio.to_thread(self.gemma_manager.load_model)
                self.gemma_loaded = True
                logger.info("Gemma model initialized for lyrics search")
            except Exception as e:
                logger.error(f"Failed to initialize Gemma: {e}")
                self.gemma_loaded = False
    
    async def search_lyrics_intelligent(self, artist: str, title: str, 
                                      transcribed_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Intelligently search for lyrics using Gemma to decide search strategy
        
        Args:
            artist: Artist name
            title: Song title
            transcribed_text: Optional transcribed text for comparison
        
        Returns:
            Search results with Gemma analysis
        """
        results = {
            "artist": artist,
            "title": title,
            "searched_at": datetime.utcnow().isoformat(),
            "search_strategy": "intelligent",
            "results": {},
            "analysis": {}
        }
        
        # Ensure Gemma is initialized
        await self.initialize_gemma()
        
        # Step 1: Search with Brave API first
        logger.info(f"Starting intelligent search for: {artist} - {title}")
        brave_result = await self.search_brave(artist, title)
        
        if brave_result:
            results["results"]["brave"] = brave_result
            
            # Step 2: Use Gemma to analyze Brave results
            if self.gemma_loaded:
                brave_quality = await self._analyze_search_quality(
                    brave_result, artist, title, "brave"
                )
                results["analysis"]["brave_quality"] = brave_quality
                
                # Step 3: Decide if we need to search Tavily
                need_tavily = await self._should_search_tavily(
                    brave_quality, brave_result
                )
                results["analysis"]["need_tavily"] = need_tavily
                
                if need_tavily:
                    logger.info("Gemma suggests searching Tavily for better results")
                    tavily_result = await self.search_tavily(artist, title)
                    
                    if tavily_result:
                        results["results"]["tavily"] = tavily_result
                        
                        # Analyze Tavily results
                        tavily_quality = await self._analyze_search_quality(
                            tavily_result, artist, title, "tavily"
                        )
                        results["analysis"]["tavily_quality"] = tavily_quality
                        
                        # Compare and select best source
                        best_source = await self._select_best_source(
                            brave_quality, tavily_quality
                        )
                        results["best_source"] = best_source
                    else:
                        results["best_source"] = "brave"
                else:
                    results["best_source"] = "brave"
            else:
                # Fallback: search both if Gemma not available
                logger.warning("Gemma not available, searching both APIs")
                tavily_result = await self.search_tavily(artist, title)
                if tavily_result:
                    results["results"]["tavily"] = tavily_result
                results["best_source"] = self._select_best_source_simple(results["results"])
        else:
            # Brave failed, try Tavily
            logger.info("Brave search failed, trying Tavily")
            tavily_result = await self.search_tavily(artist, title)
            if tavily_result:
                results["results"]["tavily"] = tavily_result
                results["best_source"] = "tavily"
        
        # Step 4: If we have transcribed text, compare with found lyrics
        if transcribed_text and results.get("best_source"):
            best_result = results["results"].get(results["best_source"])
            if best_result and self.gemma_loaded:
                comparison = await self.gemma_manager.compare_transcriptions(
                    transcribed_text,
                    best_result.get("full_content", best_result.get("snippet", ""))
                )
                results["analysis"]["transcription_comparison"] = comparison
        
        return results
    
    async def _analyze_search_quality(self, search_result: Dict, 
                                    artist: str, title: str, source: str) -> Dict:
        """Use Gemma to analyze search result quality"""
        content = search_result.get("full_content") or search_result.get("snippet", "")
        url = search_result.get("url", "")
        
        prompt = f"""Analyze this search result for the song "{title}" by {artist}:

Source: {source}
URL: {url}
Content preview: {content[:300]}

Rate the quality (1-10) and explain:
1. Does this appear to contain actual song lyrics?
2. Is it the correct song?
3. How complete are the lyrics?

Analysis:"""
        
        try:
            response = await self.gemma_manager._generate(prompt)
            
            # Parse quality score from response
            quality_score = 5  # default
            for line in response.split('\n'):
                if 'quality' in line.lower() and any(str(i) in line for i in range(1, 11)):
                    for i in range(10, 0, -1):
                        if str(i) in line:
                            quality_score = i
                            break
            
            return {
                "score": quality_score,
                "analysis": response,
                "has_lyrics": "actual song lyrics" in response.lower() or "yes" in response.lower()[:50]
            }
        except Exception as e:
            logger.error(f"Gemma analysis error: {e}")
            return {"score": 5, "analysis": "Error in analysis", "has_lyrics": True}
    
    async def _should_search_tavily(self, brave_quality: Dict, brave_result: Dict) -> bool:
        """Decide if we should search Tavily based on Brave results"""
        # If Brave score is low or doesn't have lyrics, search Tavily
        if brave_quality.get("score", 0) < 7 or not brave_quality.get("has_lyrics", False):
            return True
        
        # If Brave only has a snippet, we might want full lyrics from Tavily
        if not brave_result.get("full_content") and len(brave_result.get("snippet", "")) < 200:
            return True
        
        return False
    
    async def _select_best_source(self, brave_quality: Dict, tavily_quality: Dict) -> str:
        """Use Gemma to select the best source"""
        prompt = f"""Compare these two lyrics search results:

Brave Search:
- Quality Score: {brave_quality.get('score', 0)}/10
- Has Lyrics: {brave_quality.get('has_lyrics', False)}

Tavily Search:
- Quality Score: {tavily_quality.get('score', 0)}/10  
- Has Lyrics: {tavily_quality.get('has_lyrics', False)}

Which source is better and why? Answer with just "brave" or "tavily" followed by explanation.

Answer:"""
        
        try:
            response = await self.gemma_manager._generate(prompt)
            response_lower = response.lower()
            
            if "tavily" in response_lower[:20]:
                return "tavily"
            elif "brave" in response_lower[:20]:
                return "brave"
            else:
                # Fallback to scores
                return "tavily" if tavily_quality.get("score", 0) > brave_quality.get("score", 0) else "brave"
        except:
            return "tavily" if tavily_quality.get("score", 0) > brave_quality.get("score", 0) else "brave"
    
    def _select_best_source_simple(self, results: Dict) -> str:
        """Simple selection when Gemma not available"""
        if "tavily" in results and results["tavily"].get("lyrics"):
            return "tavily"
        elif "brave" in results:
            return "brave"
        elif "tavily" in results:
            return "tavily"
        return None
    
    async def search_brave(self, artist: str, title: str) -> Optional[Dict]:
        """Search for lyrics using Brave Search API"""
        if not self.brave_api_key:
            logger.warning("Brave API key not configured")
            return None
        
        query = f"{artist} {title} lyrics site:genius.com OR site:azlyrics.com OR site:musixmatch.com"
        
        params = {
            "q": query,
            "count": 10,
            "safesearch": "moderate"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.brave_url,
                    headers=self.brave_headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_brave_results(data, artist, title)
                    else:
                        logger.error(f"Brave API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Brave search error: {e}")
            return None
    
    async def search_tavily(self, artist: str, title: str) -> Optional[Dict]:
        """Search for lyrics using Tavily API"""
        if not self.tavily_api_key:
            logger.warning("Tavily API key not configured")
            return None
        
        query = f"{artist} {title} lyrics"
        
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "include_raw_content": True,
            "max_results": 5,
            "include_domains": ["genius.com", "azlyrics.com", "musixmatch.com", "lyrics.com"]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.tavily_url,
                    headers=self.tavily_headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_tavily_results(data, artist, title)
                    else:
                        logger.error(f"Tavily API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return None
    
    def _parse_brave_results(self, data: Dict, artist: str, title: str) -> Optional[Dict]:
        """Parse Brave search results for lyrics"""
        results = data.get("web", {}).get("results", [])
        
        for result in results:
            url = result.get("url", "")
            title_text = result.get("title", "").lower()
            description = result.get("description", "")
            
            if any(site in url for site in ["genius.com", "azlyrics.com", "musixmatch.com"]):
                if artist.lower() in title_text or title.lower() in title_text:
                    return {
                        "source": "brave",
                        "url": url,
                        "title": result.get("title"),
                        "snippet": description,
                        "site": self._extract_site_name(url),
                        "confidence": self._calculate_confidence(title_text, artist, title)
                    }
        
        return None
    
    def _parse_tavily_results(self, data: Dict, artist: str, title: str) -> Optional[Dict]:
        """Parse Tavily search results for lyrics"""
        results = data.get("results", [])
        answer = data.get("answer", "")
        
        if answer and len(answer) > 100:
            return {
                "source": "tavily",
                "lyrics": answer,
                "confidence": 0.9,
                "results": []
            }
        
        best_result = None
        highest_score = 0
        
        for result in results:
            url = result.get("url", "")
            title_text = result.get("title", "").lower()
            content = result.get("raw_content", "") or result.get("content", "")
            score = result.get("score", 0)
            
            if artist.lower() in title_text and title.lower() in title_text:
                if score > highest_score:
                    highest_score = score
                    best_result = {
                        "source": "tavily",
                        "url": url,
                        "title": result.get("title"),
                        "snippet": content[:500] if content else "",
                        "site": self._extract_site_name(url),
                        "confidence": min(score, 1.0),
                        "full_content": content
                    }
        
        return best_result
    
    def _extract_site_name(self, url: str) -> str:
        """Extract site name from URL"""
        if "genius.com" in url:
            return "Genius"
        elif "azlyrics.com" in url:
            return "AZLyrics"
        elif "musixmatch.com" in url:
            return "Musixmatch"
        elif "lyrics.com" in url:
            return "Lyrics.com"
        else:
            return "Other"
    
    def _calculate_confidence(self, text: str, artist: str, title: str) -> float:
        """Calculate confidence score for search result"""
        text_lower = text.lower()
        artist_lower = artist.lower()
        title_lower = title.lower()
        
        score = 0.5
        
        if artist_lower in text_lower:
            score += 0.25
        if title_lower in text_lower:
            score += 0.25
        
        return min(score, 1.0)

# Singleton instance
_enhanced_lyrics_manager = None

def get_enhanced_lyrics_manager() -> EnhancedLyricsSearchManager:
    """Get or create enhanced lyrics search manager instance"""
    global _enhanced_lyrics_manager
    if _enhanced_lyrics_manager is None:
        _enhanced_lyrics_manager = EnhancedLyricsSearchManager()
    return _enhanced_lyrics_manager