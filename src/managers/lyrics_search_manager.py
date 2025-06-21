# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Lyrics Search Manager using Brave and Tavily APIs
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

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LyricsSearchManager:
    def __init__(self):
        """Initialize lyrics search manager with API keys"""
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
    
    async def search_brave(self, artist: str, title: str) -> Optional[Dict]:
        """Search for lyrics using Brave Search API"""
        if not self.brave_api_key:
            logger.warning("Brave API key not configured")
            return None
        
        # Build search query
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
        
        # Build search query
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
            
            # Check if this is likely a lyrics page
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
        
        # Check if we have a direct answer with lyrics
        if answer and len(answer) > 100:
            return {
                "source": "tavily",
                "lyrics": answer,
                "confidence": 0.9,
                "results": []
            }
        
        # Parse individual results
        best_result = None
        highest_score = 0
        
        for result in results:
            url = result.get("url", "")
            title_text = result.get("title", "").lower()
            content = result.get("raw_content", "") or result.get("content", "")
            score = result.get("score", 0)
            
            # Calculate relevance
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
        
        score = 0.5  # Base score
        
        if artist_lower in text_lower:
            score += 0.25
        if title_lower in text_lower:
            score += 0.25
        
        return min(score, 1.0)
    
    async def search_lyrics(self, artist: str, title: str, 
                          source: str = "both") -> Dict[str, Any]:
        """
        Search for lyrics using specified source
        
        Args:
            artist: Artist name
            title: Song title
            source: "brave", "tavily", or "both"
        
        Returns:
            Dictionary with search results
        """
        results = {
            "artist": artist,
            "title": title,
            "searched_at": datetime.utcnow().isoformat(),
            "results": {}
        }
        
        if source in ["brave", "both"]:
            brave_result = await self.search_brave(artist, title)
            if brave_result:
                results["results"]["brave"] = brave_result
        
        if source in ["tavily", "both"]:
            tavily_result = await self.search_tavily(artist, title)
            if tavily_result:
                results["results"]["tavily"] = tavily_result
        
        # Determine best result
        if results["results"]:
            # Prefer Tavily if it has actual lyrics
            if "tavily" in results["results"] and results["results"]["tavily"].get("lyrics"):
                results["best_source"] = "tavily"
            # Otherwise use highest confidence
            else:
                best_source = max(
                    results["results"].items(),
                    key=lambda x: x[1].get("confidence", 0)
                )[0]
                results["best_source"] = best_source
        
        return results
    
    async def extract_lyrics_from_url(self, url: str) -> Optional[str]:
        """Extract lyrics from a specific URL (future enhancement)"""
        # This would require web scraping or additional API calls
        # For now, we rely on the search APIs to provide content
        logger.info(f"Lyrics extraction from URL not implemented: {url}")
        return None

# Singleton instance
_lyrics_manager = None

def get_lyrics_manager() -> LyricsSearchManager:
    """Get or create lyrics search manager instance"""
    global _lyrics_manager
    if _lyrics_manager is None:
        _lyrics_manager = LyricsSearchManager()
    return _lyrics_manager