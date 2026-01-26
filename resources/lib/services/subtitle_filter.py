def apply_filters(subtitle_list, settings, logger):
    if not subtitle_list:
        return []

    allowed_fmts = []
    if settings.get("fmt_ass"):
        allowed_fmts.append("ass")
    if settings.get("fmt_srt"):
        allowed_fmts.append("srt")
    if settings.get("fmt_ssa"):
        allowed_fmts.append("ssa")
    if settings.get("fmt_sub"):
        allowed_fmts.append("sub")
    if settings.get("fmt_sup"):
        allowed_fmts.append("sup")
    if settings.get("fmt_vtt"):
        allowed_fmts.append("vtt")

    allowed_srcs = []
    if settings.get("src_official"):
        allowed_srcs.append("official")
    if settings.get("src_reprint"):
        allowed_srcs.append("reprint")
    if settings.get("src_original"):
        allowed_srcs.append("original")
    if settings.get("src_ai"):
        allowed_srcs.append("ai")
    if settings.get("src_machine"):
        allowed_srcs.append("machine")

    allowed_langs = []
    if settings.get("lang_chs"):
        allowed_langs.append("chs")
    if settings.get("lang_cht"):
        allowed_langs.append("cht")
    if settings.get("lang_eng"):
        allowed_langs.append("eng")

    filtered_list = []
    for s in subtitle_list:
        tags = s.get("tags", {})
        t_fmt = tags.get("fmt", [])
        t_src = tags.get("source", [])
        t_lang = tags.get("lang", [])
        is_bi = tags.get("bilingual", False)

        if settings.get("bilingual") and not is_bi:
            continue

        if allowed_srcs and t_src:
            if not any(src in allowed_srcs for src in t_src):
                continue

        if allowed_langs and t_lang:
            if not any(lang in allowed_langs for lang in t_lang):
                continue

        if allowed_fmts and t_fmt:
            if not any(fmt in allowed_fmts for fmt in t_fmt):
                continue

        filtered_list.append(s)

    logger.log("SubtitleFilter", "Filtered to %d results" % len(filtered_list), level=1)
    return filtered_list
