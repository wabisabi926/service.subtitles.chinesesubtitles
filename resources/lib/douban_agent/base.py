"""
Abstract base class for Douban search agents.
"""
from abc import ABC, abstractmethod


class AbstractDoubanAgent(ABC):
    """Base class defining the interface for Douban search agents."""

    @abstractmethod
    def search(self, title, year=None, season=None):
        """
        Search Douban for movies/TV shows.
        
        Args:
            title: The title to search for
            year: Optional year to filter results
            season: Optional season number for TV shows
            
        Returns:
            List of candidate dictionaries with keys:
            - id: Douban subject ID
            - title: Title
            - year: Release year
            - type: 'movie' or 'tv'
            - label: Formatted display label
            - request_url: URL used for the search
            - origin: Original data from source
        """
        pass

    def get_search_queries(self, title, year=None, season=None):
        """Generate search queries based on title, year, and season."""
        base_query = title
        
        if season:
            season_str = str(season).strip()
            base_query = f"{title} {season_str}"

        return [base_query]

    def _format_candidate(self, id, title, year, res_type, request_url, origin):
        """Create a standardized candidate dictionary."""
        type_cn = "剧集" if res_type == "tv" else "电影"
        label = f"[{type_cn}][{title}][{year or '????'}][{id}]"

        return {
            'id': str(id),
            'title': title,
            'year': year,
            'type': res_type,
            'label': label,
            'request_url': request_url,
            'origin': origin
        }
