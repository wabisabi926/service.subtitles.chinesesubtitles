# -*- coding: utf-8 -*-

import os
import sys
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs



import archive_utils
from services.candidate_service import get_candidate
from providers.registry import build_agents
from services.download_service import download_subtitles
from services.settings import get_filter_settings
from services.subtitle_filter import apply_filters
from services.subtitle_listing import add_subtitles


__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__language__ = __addon__.getLocalizedString

__cwd__ = xbmcvfs.translatePath(__addon__.getAddonInfo('path'))
__profile__ = xbmcvfs.translatePath(__addon__.getAddonInfo('profile'))
__resource__ = xbmcvfs.translatePath(os.path.join(__cwd__, 'resources', 'lib'))
__temp__ = xbmcvfs.translatePath(os.path.join(__profile__, 'temp'))

sys.path.append(__resource__)

class Logger:
    def log(self, module, msg, level=xbmc.LOGDEBUG):
        xbmc.log("{0}::{1} - {2}".format(__scriptname__, module, msg), level=level)


class Unpacker:
    def __init__(self, logger):
        self.logger = logger

    def unpack(self, path):
        return archive_utils.unpack(path, logger=self.logger)


def Search(items):
    if items['mansearch']:
        search_str = items['mansearchstr']
    else:
        is_tv = bool(items.get('tvshow'))
        search_str = items['tvshow'] if is_tv else items['title']
    logger.log(sys._getframe().f_code.co_name, "Search for [%s], item: %s" %
               (search_str, items), level=xbmc.LOGINFO)

    candidate = get_candidate(search_str, items, logger)
    if not candidate:
        return []
    subtitle_list = []
    for provider, agent in agents.items():
        try:
            results = agent.search(items, candidate=candidate)
        except Exception as e:
            logger.log("Search", "Provider [%s] failed: %s" % (provider, e), level=xbmc.LOGWARNING)
            results = []
        for s in results or []:
            tags = s.get('tags', {})
            tags['provider'] = provider
            s['tags'] = tags
            subtitle_list.append(s)
    
    logger.log(sys._getframe().f_code.co_name, "Found %d raw results" % len(subtitle_list), level=xbmc.LOGINFO)

    if len(subtitle_list) != 0:
        settings = get_filter_settings(__addon__)
        subtitle_list = apply_filters(subtitle_list, settings, logger)
        add_subtitles(subtitle_list, __scriptid__)
    else:
        logger.log(sys._getframe().f_code.co_name, "Subtitle Not Found: %s" %
                   items, level=xbmc.LOGINFO)


def Download(url, provider=None):
    """
    Call agent download.
    """
    return download_subtitles(url, provider, agents, __addon__, __temp__, logger)


def get_params():
    param = {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        parsed = urllib.parse.parse_qs(paramstring.lstrip('?'), keep_blank_values=True)
        for key, values in parsed.items():
            param[key] = values[0]
    return param


def handle_params(params):
    if params['action'] == 'search' or params['action'] == 'manualsearch':
        # 1) Collect player info
        item = {
            'mansearch': False,
            'year': xbmc.getInfoLabel("VideoPlayer.Year"),
            'season': xbmc.getInfoLabel("VideoPlayer.Season"),
            'episode': xbmc.getInfoLabel("VideoPlayer.Episode"),
            'tvshow': xbmc.getInfoLabel("VideoPlayer.TVshowtitle"),
            'title': xbmc.getInfoLabel("VideoPlayer.Title"),
            'filename': xbmc.getInfoLabel("Player.Filename"),
            'path': xbmc.getInfoLabel("Player.Folderpath")
        }

        if 'searchstring' in params:
            item['mansearch'] = True
            item['mansearchstr'] = params['searchstring']

        # 2) Search
        Search(item)

    elif params['action'] == 'download':
        subs = Download(params["link"], params.get("provider"))
        for sub in subs:
            listitem = xbmcgui.ListItem(label=sub)
            xbmcplugin.addDirectoryItem(
                handle=int(sys.argv[1]),
                url=sub, listitem=listitem, isFolder=False)


def run():
    global agents, logger

    # Params
    params = get_params()

    logger = Logger()
    logger.log(sys._getframe().f_code.co_name, "HANDLE PARAMS：%s" % params)

    if __addon__.getSetting("proxy_follow_kodi") != "true":
        proxy = ("" if __addon__.getSetting("proxy_use") != "true"
                 else __addon__.getSetting("proxy_server"))
        os.environ["HTTP_PROXY"] = os.environ["HTTPS_PROXY"] = proxy


    # Initialize Agents
    agents = build_agents(__temp__, logger, Unpacker(logger))

    handle_params(params)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
