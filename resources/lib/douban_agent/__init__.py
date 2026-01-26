"""
Douban Agent - Search Douban for movies and TV shows

Usage:
    from douban_agent import get_agent
    
    agent = get_agent()  # Default: API-based agent
    agent = get_agent(use_legacy=True)  # Scraper-based agent (fallback)
    
    results = agent.search(title="黑客帝国", year=1999)
"""
from .base import AbstractDoubanAgent


def get_agent(use_legacy=False):
    """
    Factory method to get the appropriate Douban agent.
    
    Args:
        use_legacy: If True, uses web scraping. If False (default), uses API.
    
    Returns:
        An instance of AbstractDoubanAgent implementation.
    """
    if use_legacy:
        from .scraper_agent import ScraperAgent
        return ScraperAgent()
    else:
        from .api_agent import ApiAgent
        return ApiAgent()
