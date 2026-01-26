def _get_zimuku_agent():
    """创建一个轻量级 Zimuku agent 用于搜索候选（不需要下载功能）"""
    from providers.zimuku.agent import ZimukuAgent

    class NullLogger:
        def debug(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

        def warn(self, *args, **kwargs):
            pass

        def error(self, *args, **kwargs):
            pass

    class NullUnpacker:
        def unpack(self, path):
            return path, []

    return ZimukuAgent(None, None, NullLogger(), NullUnpacker())


def _search_douban(title, db_year, db_season, logger=None):
    candidates = []
    try:
        import douban_agent
        agent = douban_agent.get_agent()
        candidates = agent.search(title=title, year=db_year, season=db_season) or []
        if not candidates and db_year:
            if logger:
                logger.log(
                    "CandidateService",
                    "No results with year %s, retrying without year..." % db_year,
                    1,
                )
            candidates = agent.search(title=title, year=None, season=db_season) or []
    except Exception as e:
        if logger:
            logger.log("CandidateService", "Douban search failed: %s" % e, 2)
    return candidates


def _select_candidate(candidates):
    try:
        import xbmcgui
        labels = [res.get("label", res.get("title")) for res in candidates]
        sel = xbmcgui.Dialog().select("Select Candidate", labels)
        if sel == -1 or sel >= len(candidates):
            return None
        return candidates[sel]
    except (ImportError, Exception):
        return candidates[0]


def get_candidate(title, items, logger=None):
    is_tv = bool(items.get("tvshow"))
    db_year = items.get("year")
    db_season = items.get("season") if is_tv else None

    # 搜索豆瓣
    candidates = _search_douban(title, db_year, db_season, logger)

    # 搜索 Zimuku
    zimuku = _get_zimuku_agent()
    try:
        zimuku_candidates = zimuku.search_candidates(title, db_year, is_tv=is_tv)
        if zimuku_candidates:
            candidates = candidates + zimuku_candidates
    except Exception as e:
        if logger:
            logger.log("CandidateService", "Zimuku search failed: %s" % e, 2)

    # 后处理：按类型与年份排序（按来源分别处理）
    target_type = "tv" if is_tv else "movie"
    try:
        target_year = int(db_year) if db_year else None
    except Exception:
        target_year = None

    def type_key(res):
        return 0 if res.get("type") == target_type else 1

    def year_key(res):
        if target_year is None:
            return 0
        try:
            return abs(int(res.get("year")) - target_year)
        except Exception:
            return 9999

    grouped, order = {}, []
    for res in candidates:
        src = res.get("source") or "douban"
        if src not in grouped:
            grouped[src] = []
            order.append(src)
        grouped[src].append(res)

    candidates = []
    src_order = ["douban", "zimuku"]
    ordered_sources = [s for s in src_order if s in grouped]
    for s in order:
        if s not in src_order:
            ordered_sources.append(s)
    for src in ordered_sources:
        candidates.extend(sorted(grouped[src], key=lambda r: (type_key(r), year_key(r))))

    if not candidates:
        try:
            import xbmcgui
            xbmcgui.Dialog().select("Select Candidate", ["[Error] No candidates found."])
        except (ImportError, Exception):
            pass
        return None

    # 选择候选
    selected = _select_candidate(candidates)
    if not selected:
        return None

    # 如果选择了 Zimuku 来源且没有豆瓣 ID，现在获取
    if isinstance(selected, dict) and selected.get("source") == "zimuku":
        if not selected.get("id"):
            if logger:
                logger.log(
                    "CandidateService",
                    "Fetching Douban ID from %s" % selected.get("zimuku_subs_url"),
                    1,
                )
            selected["id"] = zimuku.get_douban_id_from_subs(
                selected.get("zimuku_subs_url")
            )
        if not selected.get("type"):
            selected["type"] = "tv" if is_tv else "movie"

    return selected
