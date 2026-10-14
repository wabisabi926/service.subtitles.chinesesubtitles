# -*- coding: utf-8 -*-
"""Title and filename parsing: seasons, years, release names."""
import re

CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
_CN_DIGITS = "".join(CN_NUM)  # charset of a Chinese season count
_CN_SEASON = rf'第([{_CN_DIGITS}\d]+)\s*季'
_WORD_SEASON = r'season\s*(\d+)'
SEASON_RE = re.compile(f'{_CN_SEASON}|{_WORD_SEASON}', re.I)
_CENTURY = r'(?:19|20)\d{2}'
YEAR_RE = re.compile(rf'[（(]\s*({_CENTURY})\s*[)）]')


def season_number(raw):
    """Chinese-numeral or digit season string -> int (0 when unparsable).
    Compounds through 九十九 parse: 十一 -> 11, 二十九 -> 29."""
    if raw.isdigit():
        return int(raw)
    tens, sep, ones = raw.partition("十")
    if not sep:
        return CN_NUM.get(raw, 0)
    if (not tens or tens in CN_NUM) and (not ones or ones in CN_NUM):
        return (CN_NUM[tens] if tens else 1) * 10 + (CN_NUM[ones] if ones else 0)
    return 0


def parse_meta(title):
    """Title -> (season str, year str) as carried by zimuku work titles."""
    year = season = ""
    m = YEAR_RE.search(title)
    if m:
        year, title = m.group(1), YEAR_RE.sub(" ", title)
    m = SEASON_RE.search(title)
    if m:
        season = str(season_number(m.group(1) or m.group(2)))
        if season == "0":  # unparsable season counts (garbage, 百 and up) mean none
            season = ""
    return season, year


# ---- filename parsing (fallback for unscraped media) ----

VIDEO_EXTS = (".mkv", ".mp4", ".avi", ".wmv", ".mpg", ".mpeg", ".ts", ".m2ts",
              ".mts", ".flv", ".webm", ".mov", ".iso", ".vob", ".rmvb", ".strm")

# trailing season marker in folder names: "电锯人 第一季", "Show Season 2", "Show S02"
FOLDER_SEASON_RE = re.compile(rf'(?:{_CN_SEASON}|{_WORD_SEASON}|S(\d{{1,2}}))\s*$', re.I)
# episode markers, most specific first; (?P<s>) is the season when the form carries one
EPISODE_RES = tuple(re.compile(p, re.I) for p in (
    r's(?P<s>\d{1,2})[.\s]*e(?P<e>\d{1,3})\b',
    rf'第(?P<s>[{_CN_DIGITS}\d]+)季.*?第\s*(?P<e>\d+)\s*集',
    r'\bep?(?P<e>\d{1,3})\b',
    r'第\s*(?P<e>\d{1,3})\s*[集话話]',
    # fansub "[Group] Title - 03 [BD]" / "- 03v2": the spaced dash excludes
    # DTS-HD, the lookahead excludes "- 1080p" and "- 5.1"
    r'(?:^|[\s_])-[\s_]*(?P<e>\d{1,3})(?:v\d)?(?=[\s_\[(]|\.(?!\d)|$)',
))
YEAR_TOKEN_RE = re.compile(rf'^{_CENTURY}$')


def _episode(name):
    """(season, episode, start) of the first marker in a name: season is
    None for a bare episode form, everything None without a marker."""
    for regex in EPISODE_RES:
        m = regex.search(name)
        if m:
            season = m.groupdict().get("s")
            return (season_number(season) if season else None), int(m.group("e")), m.start()
    return None, None, None


def episode_marker(name):
    """(season, episode) ints carried by a filename; either may be None."""
    return _episode(name)[:2]

# release tags stripped from parsed titles, grouped by what they describe;
# the sub runs on tokens already split on . _ - space, so only dot-free
# spellings can occur (h264, never h.264)
JUNK_TAGS = {
    "resolution": ("720p", "1080p", "1080i", "2160p", "4k"),
    "codec": ("x264", "x265", "h264", "h265", "hevc", "avc"),
    "source": ("bluray", "bdrip", "brrip", "webdl", "webrip", "web",
               "hdtv", "dvdrip", "remux", "hdrip"),
    "platform": ("amzn", "nf"),
    "audio": ("dd", "ddp", "dd5", "dd51", "ddp5", "ddp51"),
    "edition": ("proper", "repack", "internal", "limited", "extended", "complete"),
    "range": ("8bit", "10bit", "hdr", "hdr10", "dv"),
}


def _any_of(tags):
    """Literal-tag alternation, longest first so 'webdl' is not
    half-stripped by 'web'."""
    return "|".join(re.escape(t) for t in sorted(tags, key=len, reverse=True))


RELEASE_JUNK_RE = re.compile(_any_of(sum(JUNK_TAGS.values(), ())), re.I)


def parse_filename(name):
    """Extract {title, year, season, episode} from a release filename.

    Rules applied in order: the first episode marker (title stops there),
    a standalone (19|20)xx token as year (title stops there), then separator
    '.'/'_'/'-'/' ' -> space and best-effort release-tag stripping (residue
    like a lone 'DL' can survive in files without year or episode markers).
    Fields stay empty when nothing parses.
    """
    out = {"title": "", "year": "", "season": "", "episode": ""}
    name = (name or "").strip()
    if name.lower().endswith(VIDEO_EXTS):  # only a real extension; "Show.2024" keeps its year
        name = name[:name.rfind(".")]
    if not name:
        return out

    season, episode, start = _episode(name)
    if episode is not None:
        out["season"], out["episode"] = str(season or ""), str(episode)
        name = name[:start]

    tokens = re.split(r"[.\-_ ]+", name)
    for i, token in enumerate(tokens):
        if YEAR_TOKEN_RE.match(token):
            out["year"] = token
            tokens = tokens[:i]
            break
    out["title"] = " ".join(filter(None, (RELEASE_JUNK_RE.sub("", t) for t in tokens))).strip()
    return out
