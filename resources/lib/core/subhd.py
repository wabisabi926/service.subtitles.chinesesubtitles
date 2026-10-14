# -*- coding: utf-8 -*-
"""SubHD (subhd.tv) subtitle provider."""
import re
import urllib.parse

from bs4 import BeautifulSoup

from .archive import save_and_extract
from .http import filename_from_headers, make_session, noop_log
from .matcher import episode_marker
from .models import FORMATS, DownloadResult, Subtitle, Tags

# Chinese origin badge -> normalized source tag
SOURCE_MAP = {"转载精修": "reprint", "官方字幕": "official", "原创翻译": "original",
              "机器翻译": "machine", "AI翻润色": "ai"}


class SubhdProvider:
    BASE_URL = "https://subhd.tv"

    def __init__(self, log=noop_log, backend=None):
        self.log = log
        self.backend = backend  # archive backend for rar/7z (Kodi vfs)
        self.session = make_session()

    def _get(self, url, referer=None):
        try:
            resp = self.session.get(url, headers={"Referer": referer} if referer else {}, timeout=10)
            if resp.status_code == 200:
                return resp.content
            self.log(f"subhd: GET {url} -> HTTP {resp.status_code}")
        except Exception as e:
            self.log(f"subhd: GET {url} failed: {e}")
        return None

    # ---- search ----

    def search(self, query, work):
        """List the subtitles of the work's /d/{douban id} page."""
        href = work.anchors.get("subhd")
        if not href:
            return []
        content = self._get(urllib.parse.urljoin(self.BASE_URL, href))
        if not content:
            return []
        return self._parse_list(content, query.episode if query.is_tv else None)

    def _parse_list(self, content, target_episode=None):
        """Parse the work page; bg-light headers split movie/collection/episode rows."""
        soup = BeautifulSoup(content, "html.parser")
        container = soup.select_one("div.bg-white.shadow-sm.rounded-3.mb-5")
        if not container:
            return []
        results, category = [], None
        for child in container.children:
            if child.name != "div":
                continue
            classes = child.get("class", [])
            if "bg-light" in classes:
                text = child.get_text()
                category = "collection" if "合集" in text else episode_marker(text)[1]
            elif "row" in classes:
                is_collection = category == "collection"
                if target_episode and not is_collection and category != int(target_episode):
                    continue
                link = child.select_one("a.link-dark")
                if not link or not link.get("href", "").startswith("/a/"):
                    continue
                tags = self._parse_tags(child.find_all("span"))
                tags.collection = is_collection
                fansub = child.select_one('a[href^="/zu/"]') or child.select_one('a[href^="/u/"]')
                tags.fansub = fansub.get_text().strip() if fansub else ""
                results.append(Subtitle(link.get_text().strip(), self.BASE_URL + link["href"], tags))
        return results

    def _parse_tags(self, spans):
        tags = Tags()
        for span in spans:
            classes = span.get("class", [])
            text = span.get_text().strip()
            if "rounded" in classes and "text-white" in classes:
                for cn, key in SOURCE_MAP.items():
                    if cn in text:
                        tags.source.append(key)
                        break
            if "fw-bold" in classes:
                if "简体" in text: tags.lang.append("chs")
                if "繁体" in text: tags.lang.append("cht")
                if "英语" in text: tags.lang.append("eng")
                if "双语" in text: tags.bilingual = True
            if "text-secondary" in classes:
                for fmt in FORMATS:
                    if fmt.upper() in text.upper():
                        tags.fmt.append(fmt)
                        break
        return tags

    # ---- download ----

    def _resolve_down_url(self, page_url, soup):
        """Resolve the one-time temp download page.

        Since the 2026-08 redesign the detail page has no download link;
        a button (button.down[data-sid]) must be exchanged for a /down/{sid}
        temp page via POST /api/sub/prepare-download (direct /down/{sid}
        returns 403). The old <a class="down"> links are gone from the page.
        """
        sid = None
        button = soup.find("button", class_="down")
        if button:
            sid = button.get("data-sid") or button.get("sid")
        if not sid:
            match = re.search(r"/a/([^/?#]+)", page_url)
            sid = match.group(1) if match else None
        if sid:
            try:
                resp = self.session.post(
                    self.BASE_URL + "/api/sub/prepare-download",
                    json={"sid": sid},
                    headers={"Referer": page_url, "X-Requested-With": "XMLHttpRequest"},
                    timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("url"):
                        url = data["url"]
                        return url if url.startswith("http") else self.BASE_URL + url
                    self.log(f"subhd: prepare-download failed: {data.get('msg')}")
                else:
                    self.log(f"subhd: prepare-download HTTP {resp.status_code}")
            except Exception as e:
                self.log(f"subhd: prepare-download failed: {e}")
        return None

    def download(self, link, dest):
        """Fetch, extract and store one subtitle into dest."""
        content = self._get(link)
        if not content:
            return DownloadResult()
        soup = BeautifulSoup(content, "html.parser")
        down_url = self._resolve_down_url(link, soup)
        if not down_url:
            self.log("subhd: no download entry found on page")
            return DownloadResult()
        # the temp page must be visited once before the POST: skipping this
        # GET fails the API with "temp page expired" (measured)
        if not self._get(down_url, referer=link):
            return DownloadResult()
        sid = down_url.split("/")[-1].split("?")[0].split("#")[0]
        api_url = self.BASE_URL + "/api/sub/down"
        try:
            resp = self.session.post(api_url, json={"sid": sid, "cap": ""},
                                     headers={"Referer": down_url}, timeout=10)
            if resp.status_code != 200:
                return DownloadResult()
            data = resp.json()
            if data.get("pass") is False:
                # throttle refusal, plain text like '下载频率过高，请不要再试'
                # (the old-site SVG captcha is gone: no captcha code remains
                # in the site's JS bundles); the one-time temp page is spent,
                # so retrying only draws 'temp page expired' — report and stop
                msg = data.get("msg")
                self.log(f"subhd: download refused: {msg}")
                return DownloadResult(reason=f"SubHD: {msg}")
            if not data.get("success"):
                return DownloadResult()
            file_url = data.get("url")
            if not file_url:
                return DownloadResult()
            if not file_url.startswith("http"):
                file_url = self.BASE_URL + file_url
            file_resp = self.session.get(file_url, headers={"Referer": down_url}, timeout=15)
            if file_resp.status_code != 200:
                self.log(f"subhd: file GET -> HTTP {file_resp.status_code}")
                return DownloadResult()
            filename = filename_from_headers(
                file_resp.headers.get("Content-Disposition"),
                url=file_resp.url or file_url, default="subtitle.bin")
            return save_and_extract(dest, filename, file_resp.content, self.backend)
        except Exception as e:
            self.log(f"subhd: download failed: {e}")
            return DownloadResult()
