def get_filter_settings(addon):
    return {
        "bilingual": addon.getSetting("filter_bilingual") == "true",
        "src_official": addon.getSetting("filter_src_official") == "true",
        "src_reprint": addon.getSetting("filter_src_reprint") == "true",
        "src_original": addon.getSetting("filter_src_original") == "true",
        "src_ai": addon.getSetting("filter_src_ai") == "true",
        "src_machine": addon.getSetting("filter_src_machine") == "true",
        "lang_chs": addon.getSetting("filter_lang_chs") == "true",
        "lang_cht": addon.getSetting("filter_lang_cht") == "true",
        "lang_eng": addon.getSetting("filter_lang_eng") == "true",
        "fmt_ass": addon.getSetting("filter_fmt_ass") == "true",
        "fmt_srt": addon.getSetting("filter_fmt_srt") == "true",
        "fmt_ssa": addon.getSetting("filter_fmt_ssa") == "true",
        "fmt_sub": addon.getSetting("filter_fmt_sub") == "true",
        "fmt_sup": addon.getSetting("filter_fmt_sup") == "true",
        "fmt_vtt": addon.getSetting("filter_fmt_vtt") == "true",
    }
