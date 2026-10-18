# -*- coding: utf-8 -*-
"""Live tests for the SubHD provider: direct /d/{douban id} search, download."""
import os
import sys
import tempfile

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
lib_dir = os.path.join(base_dir, "resources", "lib")
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

from core.models import Work, WorkQuery, build_label
from core.subhd import SubhdProvider

# Friends S1's Douban subject id: SubHD serves work pages under it directly
FRIENDS_S1_DOUBAN = "1393859"


def test_subhd_parse_list_splits_by_header(monkeypatch):
    html = """
    <div class="bg-white shadow-sm rounded-3 mb-5">
      <div class="bg-light">合集</div>
      <div class="row"><a class="link-dark" href="/a/AAA">Pack.S01</a>
        <span class="rounded text-white">官方字幕</span><span class="fw-bold">简体 英语 双语</span>
        <span class="text-secondary">SRT</span><a href="/zu/1">组</a></div>
      <div class="bg-light">第 03 集</div>
      <div class="row"><a class="link-dark" href="/a/BBB">Ep3.srt</a>
        <span class="fw-bold">繁体</span><span class="text-secondary">ASS</span><a href="/u/2">user</a></div>
      <div class="bg-light">第5集</div>
      <div class="row"><a class="link-dark" href="/a/CCC">Ep5.srt</a></div>
      <div class="row"><a class="link-dark" href="/x/ad">advert</a></div>
    </div>
    """
    provider = SubhdProvider()
    monkeypatch.setattr(provider, "_get", lambda url, referer=None: html.encode())
    work = Work(title="Show", anchors={"subhd": "/d/1"})
    subs = provider.search(WorkQuery(title="Show", season="1", episode="3", is_tv=True), work)
    pack, episode = subs
    assert (pack.filename, pack.link, pack.tags.collection) == ("Pack.S01", "https://subhd.tv/a/AAA", True)
    assert (pack.tags.src, pack.tags.lang, pack.tags.bilingual, pack.tags.fmt, pack.tags.fansub) == \
        (["official"], ["chs", "eng"], True, ["srt"], "组")
    assert (episode.filename, episode.tags.collection, episode.tags.lang, episode.tags.fansub) == \
        ("Ep3.srt", False, ["cht"], "user")
    everything = provider.search(WorkQuery(title="Show"), work)
    assert [s.filename for s in everything] == ["Pack.S01", "Ep3.srt", "Ep5.srt"]


def test_subhd_search_and_download():
    log = lambda msg: print(f"  [subhd] {msg}")
    provider = SubhdProvider(log=log)

    print("\n=== SubHD direct /d/{douban id}: Friends S1 ===")
    query = WorkQuery(title="老友记 Friends", season="1", is_tv=True)
    work = Work(title="老友记 第一季 Friends", season="1",
                anchors={"subhd": f"/d/{FRIENDS_S1_DOUBAN}"})
    results = provider.search(query, work)
    assert results, "SubHD direct douban-id page returned no subtitles."
    print(f"Total subtitles found: {len(results)}")
    for i, s in enumerate(results[:5]):
        print(f"[{i:2}] {build_label(s.tags, filename=s.filename)}")

    print("\n=== Downloading first subtitle ===")
    with tempfile.TemporaryDirectory() as dest:
        result = provider.download(results[0].link, dest)
        print(f"status={result.status} files={result.files}")
        assert result.status == "ok" and result.files, "SubHD download failed."
        assert all(os.path.exists(p) for p in result.paths)
