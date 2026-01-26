
import os
import sys
import tempfile
from unittest.mock import MagicMock

# Add lib to path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
lib_dir = os.path.join(base_dir, "resources", "lib")
if lib_dir not in sys.path:
    sys.path.append(lib_dir)
from providers.subhd import SubHDAgent
from providers.common import build_subtitle_label
from douban_agent import get_agent

class RealLogger:
    def log(self, module, msg, level=0):
        print(f"[{module}] {msg}")

def _build_agent(dl_loc):
    logger = RealLogger()
    unpacker = MagicMock()
    unpacker.unpack.return_value = ("", [])
    
    # Base URL for SubHD
    agent = SubHDAgent("https://subhd.tv", dl_loc, logger, unpacker)
    return agent, logger


def test_subhd_search_and_download():
    with tempfile.TemporaryDirectory() as dl_loc:
        agent, logger = _build_agent(dl_loc)

        print("\n=== Testing SubHD Search for Breaking Bad S02E05 ===")
        items = {
            'tvshow': 'Breaking Bad',
            'season': '2',
            'episode': '5',
            'year': '2009'
        }

        douban = get_agent(use_legacy=False)
        candidates = douban.search("Breaking Bad", year=2009, season=2)
        assert candidates, "Douban candidate search returned no results."
        selected = candidates[0]

        results = agent.search(items, candidate=selected)
        assert isinstance(results, list)
        assert results, "SubHD search returned no subtitles."

        print(f"\nTotal subtitles found: {len(results)}")
        print("-" * 50)

        for i, s in enumerate(results[:5]):
            tags = s.get('tags', {})
            final_label = build_subtitle_label(tags, provider="SUBHD", filename=s.get('filename'))
            print(f"[{i:2}] {final_label}")
        print("-" * 50)

        print("\n=== Downloading first subtitle ===")
        first = results[0]
        names, short_names, paths = agent.download(first["link"])
        print(f"Downloaded: {names}")
        print(f"Short names: {short_names}")
        print(f"Paths: {paths}")


if __name__ == "__main__":
    test_subhd_search_and_download()
