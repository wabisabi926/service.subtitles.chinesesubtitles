import os

import xbmcgui
import xbmcvfs


def download_subtitles(url, provider, agents, addon, temp_dir, logger):
    if not xbmcvfs.exists(temp_dir.replace("\\", "/")):
        xbmcvfs.mkdirs(temp_dir)
    dirs, files = xbmcvfs.listdir(temp_dir)
    for file in files:
        xbmcvfs.delete(os.path.join(temp_dir, file))

    logger.log("Download", "Download page: %s" % url, level=1)

    dl_agent = agents.get(provider or "subhd", agents.get("subhd"))
    sub_name_list, short_sub_name_list, sub_file_list = dl_agent.download(url)
    logger.log("Download", "Files: %s" % sub_name_list, level=1)

    if len(sub_name_list) == 0:
        return []
    if len(sub_name_list) == 1:
        selected_sub = sub_file_list[0]
    else:
        cut_fn = addon.getSetting("cutsubfn")
        display_list = short_sub_name_list if cut_fn == "true" else sub_name_list
        sel = xbmcgui.Dialog().select("Choose Subtitle", display_list)
        if sel == -1:
            sel = 0
        selected_sub = sub_file_list[sel]

    logger.log("Download", "SUB FILE TO USE: %s" % selected_sub, level=1)
    return [selected_sub]
