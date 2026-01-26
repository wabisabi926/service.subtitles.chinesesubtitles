import sys

import xbmcgui
import xbmcplugin

from providers.common import build_subtitle_label


def add_subtitles(subtitle_list, scriptid):
    for s in subtitle_list:
        tags = s.get("tags", {})
        final_label = build_subtitle_label(tags, filename=s.get("filename"))

        provider = tags.get("provider")
        if provider:
            final_label = f"[{provider.upper()}]{final_label}"

        listitem = xbmcgui.ListItem(label=s["language_name"], label2=final_label)
        listitem.setArt({
            "icon": s["rating"],
            "thumb": s["language_flag"],
        })
        listitem.setProperty("sync", "false")
        listitem.setProperty("hearing_imp", "false")

        url = "plugin://%s/?action=download&link=%s" % (scriptid, s["link"])
        if provider:
            url += f"&provider={provider}"
        xbmcplugin.addDirectoryItem(
            handle=int(sys.argv[1]),
            url=url,
            listitem=listitem,
            isFolder=False,
        )
