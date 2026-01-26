"""
Scraper-based Douban agent using www.douban.com/search (legacy method)
"""
from .base import AbstractDoubanAgent
import re
import requests
from bs4 import BeautifulSoup


class ScraperAgent(AbstractDoubanAgent):
    """
    Douban search agent using traditional web scraping.
    This is the fallback/legacy implementation.
    """

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.douban.com/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.douban.com/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def search(self, title, year=None, season=None):
        """Search Douban and return a list of candidates."""
        search_queries = self.get_search_queries(title, year, season)
        candidates = []
        seen_ids = set()

        for query in search_queries:
            if candidates:
                break

            try:
                resp = self.session.get(self.base_url, params={"cat": "1002", "q": query}, timeout=10)
                if resp.status_code != 200:
                    continue

                for result in self._parse_results(resp):
                    if result['id'] not in seen_ids:
                        seen_ids.add(result['id'])
                        candidates.append(result)
            except Exception:
                pass

        return candidates

    def _parse_results(self, response):
        """Parse search results from HTML response."""
        results = []
        soup = BeautifulSoup(response.text, 'html.parser')

        for res in soup.select('.result'):
            title_tag = res.select_one('.content .title a')
            if not title_tag:
                continue

            # Extract ID from onclick or href
            sid = self._extract_id(title_tag)
            if not sid:
                continue

            # Determine type
            res_type = self._extract_type(res)
            if res_type == "unknown":
                continue

            # Extract year
            res_year = self._extract_year(res)

            results.append(self._format_candidate(
                id=sid,
                title=title_tag.get_text().strip(),
                year=res_year,
                res_type=res_type,
                request_url=response.url,
                origin=str(res)
            ))

        return results

    def _extract_id(self, title_tag):
        """Extract Douban subject ID from title element."""
        onclick = title_tag.get('onclick', '')
        match = re.search(r'sid: (\d+)', onclick)
        if match:
            return match.group(1)

        href = title_tag.get('href', '')
        match = re.search(r'subject/(\d+)', href)
        return match.group(1) if match else None

    def _extract_type(self, result_element):
        """Extract content type (movie/tv) from result element."""
        title_area = result_element.select_one('.content .title h3')
        if title_area:
            first_span = title_area.select_one('span')
            if first_span:
                txt = first_span.get_text()
                if "[电影]" in txt:
                    return "movie"
                elif "[电视剧]" in txt:
                    return "tv"
        return "unknown"

    def _extract_year(self, result_element):
        """Extract year from result element metadata."""
        meta_tag = result_element.select_one('.subject-cast')
        if meta_tag:
            match = re.search(r'(\d{4})', meta_tag.get_text())
            return match.group(1) if match else None
        return None
