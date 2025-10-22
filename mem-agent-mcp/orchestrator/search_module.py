"""
Search Module - Web Search Integration

Single Responsibility: Search the web for current, real-world data

This module provides web search capabilities to dramatically improve plan quality.
Plans get real current data instead of being based only on templates and memory.

Key benefits:
- Current market statistics
- Real company examples
- Industry trends
- Expert insights
- Concrete case studies
"""

import os
import json
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SearchResult:
    """Standard format for search results"""
    title: str
    url: str
    snippet: str
    source: str


class SearchModule:
    """Handles web search operations"""

    def __init__(self):
        """
        Initialize search module

        Supports multiple search providers:
        - DuckDuckGo (free, no API key needed)
        - SerpAPI (paid, requires API key)
        - Brave Search (free tier available)

        Falls back gracefully if no provider available
        """
        self.provider = self._detect_provider()

    def _detect_provider(self) -> str:
        """Detect which search provider to use"""
        # Check for API keys in environment
        if os.getenv("SERPAPI_API_KEY"):
            return "serpapi"
        elif os.getenv("BRAVE_API_KEY"):
            return "brave"
        else:
            # Try DuckDuckGo (no API key needed)
            try:
                import duckduckgo_search
                return "duckduckgo"
            except ImportError:
                return "none"

    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Search the web for current information

        Args:
            query: Search query (e.g., "healthcare market analysis 2025")
            num_results: Number of results to return (default: 5)

        Returns:
            List of SearchResult objects with title, url, snippet, source
        """
        if self.provider == "duckduckgo":
            return self._search_duckduckgo(query, num_results)
        elif self.provider == "serpapi":
            return self._search_serpapi(query, num_results)
        elif self.provider == "brave":
            return self._search_brave(query, num_results)
        else:
            print(f"   ⚠️ No search provider available. Install duckduckgo-search or set API keys.")
            return []

    def _search_duckduckgo(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using DuckDuckGo (free, no API key)"""
        try:
            from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=num_results):
                    results.append(SearchResult(
                        title=r.get('title', 'No title'),
                        url=r.get('href', 'No URL'),
                        snippet=r.get('body', 'No snippet'),
                        source='DuckDuckGo'
                    ))
            return results
        except Exception as e:
            print(f"   ⚠️ DuckDuckGo search failed: {e}")
            return []

    def _search_serpapi(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using SerpAPI (requires API key)"""
        try:
            import requests

            api_key = os.getenv("SERPAPI_API_KEY")
            url = "https://serpapi.com/search"

            params = {
                "q": query,
                "api_key": api_key,
                "num": num_results
            }

            response = requests.get(url, params=params)
            data = response.json()

            results = []
            for r in data.get('organic_results', []):
                results.append(SearchResult(
                    title=r.get('title', 'No title'),
                    url=r.get('link', 'No URL'),
                    snippet=r.get('snippet', 'No snippet'),
                    source='SerpAPI'
                ))
            return results
        except Exception as e:
            print(f"   ⚠️ SerpAPI search failed: {e}")
            return []

    def _search_brave(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using Brave Search API (requires API key)"""
        try:
            import requests

            api_key = os.getenv("BRAVE_API_KEY")
            url = "https://api.search.brave.com/res/v1/web/search"

            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key
            }

            params = {
                "q": query,
                "count": num_results
            }

            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            results = []
            for r in data.get('web', {}).get('results', []):
                results.append(SearchResult(
                    title=r.get('title', 'No title'),
                    url=r.get('url', 'No URL'),
                    snippet=r.get('description', 'No snippet'),
                    source='Brave Search'
                ))
            return results
        except Exception as e:
            print(f"   ⚠️ Brave Search failed: {e}")
            return []


# Example usage
if __name__ == "__main__":
    search = SearchModule()
    results = search.search("healthcare market analysis 2025", num_results=3)

    print(f"Found {len(results)} results:")
    for r in results:
        print(f"\n**{r.title}**")
        print(f"{r.snippet}")
        print(f"Source: {r.url}")
