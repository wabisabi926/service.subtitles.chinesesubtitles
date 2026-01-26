"""
API-based Douban agent using search.douban.com/movie/subject_search
"""
from .base import AbstractDoubanAgent
import re
import json
import urllib.request
import urllib.parse
import ssl


class ApiAgent(AbstractDoubanAgent):
    """
    Douban search agent using the official search.douban.com API endpoint.
    This is the primary/default implementation.
    """

    def __init__(self):
        super().__init__()
        self.base_url = "https://search.douban.com/movie/subject_search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://movie.douban.com/'
        }
        self.ssl_context = ssl._create_unverified_context()

    def search(self, title, year=None, season=None):
        """Search Douban and return a list of candidates."""
        search_queries = self.get_search_queries(title, year, season)
        candidates = []
        seen_ids = set()

        for query in search_queries:
            if candidates:
                break

            for result in self._fetch_search_results(query):
                if result['id'] not in seen_ids:
                    seen_ids.add(result['id'])
                    candidates.append(result)

        return candidates

    def _fetch_search_results(self, query):
        """Fetch results with pagination (up to 5 pages / 75 results)."""
        all_results = []
        max_pages, page_size = 5, 15

        for page in range(max_pages):
            params = {
                "search_text": query,
                "cat": "1002",
                "start": str(page * page_size)
            }
            full_url = f"{self.base_url}?{urllib.parse.urlencode(params)}"

            try:
                req = urllib.request.Request(full_url, headers=self.headers)
                with urllib.request.urlopen(req, context=self.ssl_context, timeout=10) as response:
                    if response.status != 200:
                        break

                    items = self._parse_html(response.read().decode('utf-8'), full_url)
                    if not items:
                        break

                    all_results.extend(items)
                    if len(items) < page_size:
                        break
            except Exception:
                break

        return all_results

    def _parse_html(self, html, request_url):
        """Extract items from window.__DATA__ JSON embedded in HTML."""
        items = []
        match = re.search(r'window\.__DATA__\s*=\s*({.+?});', html, re.DOTALL)
        if not match:
            return items

        try:
            data = json.loads(match.group(1).strip())

            for item in data.get('items', []):
                if item.get('tpl_name') != 'search_subject':
                    continue

                sid = item.get('id')
                if not sid:
                    continue

                full_title = item.get('title', '').strip()

                # Extract year from title (e.g. "Title (2024)")
                year_match = re.search(r'\((\d{4})\)', full_title)
                res_year = year_match.group(1) if year_match else None

                # Determine type from more_url
                more_url = item.get('more_url', '')
                res_type = "tv" if "is_tv:'1'" in more_url else "movie"

                items.append(self._format_candidate(
                    id=sid,
                    title=full_title.replace(f"({res_year})", "").strip() if res_year else full_title,
                    year=res_year,
                    res_type=res_type,
                    request_url=request_url,
                    origin=item
                ))
        except Exception:
            pass

        return items
