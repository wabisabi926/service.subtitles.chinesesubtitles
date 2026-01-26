import os
import sys

# Ensure resources/lib is in path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
lib_dir = os.path.join(base_dir, "resources", "lib")
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

from douban_agent import get_agent


def _run_douban_search(agent_label, agent):
    results = agent.search("黑客帝国", year=1999)
    assert isinstance(results, list)
    assert results, "Douban search returned no candidates."

    first = results[0]
    print(f"\n=== Douban candidate search ({agent_label}) ===")
    print("Total candidates:", len(results))
    for i, res in enumerate(results[:5], start=1):
        print(
            f"{i}. id={res.get('id')} | title={res.get('title')} | "
            f"year={res.get('year')} | type={res.get('type')} | "
            f"label={res.get('label')}"
        )
    assert first.get("id"), "Candidate missing id."
    assert first.get("title"), "Candidate missing title."
    assert first.get("origin") is not None, "Candidate missing origin."


def test_douban_candidate_search_api():
    _run_douban_search("api", get_agent(use_legacy=False))


def test_douban_candidate_search_legacy():
    _run_douban_search("legacy", get_agent(use_legacy=True))
