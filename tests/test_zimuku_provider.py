
import os
import sys
import tempfile
from unittest.mock import MagicMock

# Add lib to path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
lib_dir = os.path.join(base_dir, "resources", "lib")
if lib_dir not in sys.path:
    sys.path.append(lib_dir)
from providers.zimuku import ZimukuAgent
from providers.common import build_subtitle_label

class RealLogger:
    def log(self, module, msg, level=0):
        print(f"[{module}] {msg}")

def _build_agent(dl_loc):
    logger = RealLogger()
    unpacker = MagicMock()
    unpacker.unpack.return_value = ("", [])
    
    agent = ZimukuAgent("https://zimuku.org", dl_loc, logger, unpacker)
    return agent, logger


def test_zimuku_candidate_search():
    with tempfile.TemporaryDirectory() as dl_loc:
        agent, _logger = _build_agent(dl_loc)
        candidates = agent.search_candidates("电锯人", "2022", is_tv=True)
        assert isinstance(candidates, list)
        assert candidates, "Zimuku candidate search returned no results."
        first = candidates[0]
        print("\n=== Zimuku candidate search ===")
        print("Total candidates:", len(candidates))
        for i, res in enumerate(candidates[:5], start=1):
            print(
                f"{i}. title={res.get('title')} | year={res.get('year')} | "
                f"type={res.get('type')} | url={res.get('zimuku_subs_url')}"
            )
        assert first.get("zimuku_subs_url"), "Candidate missing zimuku_subs_url."


def test_zimuku_search_and_download():
    with tempfile.TemporaryDirectory() as dl_loc:
        agent, logger = _build_agent(dl_loc)

        print("\n=== Testing Zimuku Search for 电锯人 S01E02 ===")
        items = {
            'tvshow': '电锯人',
            'season': '1',
            'episode': '2',
            'year': '2022'
        }

        candidates = agent.search_candidates("电锯人", "2022", is_tv=True)
        assert candidates, "Zimuku candidate search returned no results."
        selected = candidates[0]
        if not selected.get("id"):
            selected["id"] = agent.get_douban_id_from_subs(selected.get("zimuku_subs_url"))
        if not selected.get("type"):
            selected["type"] = "tv"

        results = agent.search(items, candidate=selected)
        assert isinstance(results, list)
        assert results, "Zimuku search returned no subtitles."

        print(f"\nTotal subtitles found: {len(results)}")
        print("-" * 50)

        for i, s in enumerate(results[:5]):
            tags = s.get('tags', {})
            final_label = build_subtitle_label(tags, provider="ZIMUKU", filename=s.get('filename'))

            print(f"[{i:2}] {final_label}")
        print("-" * 50)
        print("\n=== Downloading first subtitle ===")
        first = results[0]
        names, short_names, paths = agent.download(first["link"])
        print(f"Downloaded: {names}")
        print(f"Short names: {short_names}")
        print(f"Paths: {paths}")


if __name__ == "__main__":
    test_zimuku_candidate_search()
    test_zimuku_search_and_download()
