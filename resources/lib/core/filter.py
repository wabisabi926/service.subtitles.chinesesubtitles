# -*- coding: utf-8 -*-
"""Filter and rank subtitles according to user settings."""
from .http import noop_log
from .models import FILTER_GROUPS, SOURCES


def sort_key(subtitle):
    """Simplified-Chinese bilingual first, then by source quality."""
    tags = subtitle.tags
    langs = set(tags.lang)
    if "chs" in langs and tags.bilingual:
        lang_tier = 0
    elif "chs" in langs:
        lang_tier = 1
    elif "cht" in langs and tags.bilingual:
        lang_tier = 2
    elif "cht" in langs:
        lang_tier = 3
    else:
        lang_tier = 4
    src_tier = min((SOURCES.index(s) for s in tags.src if s in SOURCES), default=len(SOURCES))
    return (lang_tier, src_tier)


def apply_filters(subtitles, settings, log=noop_log):
    """Drop subtitles disallowed by settings, then sort by preference.

    A subtitle passes a group (source, language, format) when it carries no
    tag of that group, when the whole group is switched off, or when one of
    its tags is enabled; 'bilingual' is the only hard filter.
    """
    enabled = {group: {k for k in vocab if settings.get(f"{group}_{k}")}
               for group, vocab in FILTER_GROUPS.items()}

    def passes(tags):
        if settings.get("bilingual") and not tags.bilingual:
            return False
        for group, want in enabled.items():
            have = getattr(tags, group)
            if want and have and want.isdisjoint(have):
                return False
        return True

    kept = sorted((s for s in subtitles if passes(s.tags)), key=sort_key)
    log(f"filtered {len(kept)}/{len(subtitles)} subtitles")
    return kept
