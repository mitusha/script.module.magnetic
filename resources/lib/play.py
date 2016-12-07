# coding: utf-8
# Name:        play.py
# Author:      Mancuniancol
# Created on:  28.11.2016
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Play a link from torrent or magnet
"""
from json import loads
from urllib2 import Request, urlopen

import xbmcgui

from dialog_select import DialogSelect
from provider import *
from utils import string

ADDON = xbmcaddon.Addon()
ADDON_PATH = ADDON.getAddonInfo("path")


def play(magnet):
    """
    Play a magnet or torrent
    :param magnet: magnet or torrent to be played
    :type magnet: str
    """
    plugin = get_setting('plugin')
    uri_string = get_playable_link(magnet)
    if plugin == 'Quasar':
        link = 'plugin://plugin.video.quasar/play?uri=%s' % uri_string

    elif plugin == 'Pulsar':
        link = 'plugin://plugin.video.pulsar/play?uri=%s' % uri_string

    elif plugin == 'KmediaTorrent':
        link = 'plugin://plugin.video.kmediatorrent/play/%s' % uri_string

    elif plugin == "Torrenter":
        link = 'plugin://plugin.video.torrenter/?action=playSTRM&url=' + uri_string + \
               '&not_download_only=True'

    elif plugin == "YATP":
        link = 'plugin://plugin.video.yatp/?action=play&torrent=' + uri_string

    else:
        link = 'plugin://plugin.video.xbmctorrent/play/%s' % uri_string

    # play media
    xbmc.executebuiltin("PlayMedia(%s)" % link)
    xbmc.executebuiltin('Dialog.Close(all, true)')


def search(info=None):
    # request data
    operation = info.get('search', '')
    query = info.get('title', '')
    title = quote_plus(query)
    payload = ''

    if operation == 'general':
        payload = '?search=general&title=%s' % title

    elif operation == "movie":
        year = info.get('year', '')
        imdb_id = info.get('imdb', '')
        payload = '?search=movie&imdb=%s&title=%s&year=%s' % (imdb_id, title, year)

    elif operation == "episode":
        season = info.get('season', '')
        episode = info.get('episode', '')
        payload = '?search=episode&title=%s&season=%s&episode=%s' % (title, season, episode)

    elif operation == "season":
        season = info.get('season', '')
        payload = '?search=episode&title=%s&season=%s' % (title, season)

    magnetic_url = "http://%s:%s" % (str(PROVIDER_SERVICE_HOST), str(PROVIDER_SERVICE_PORT))
    url = magnetic_url + payload
    logger.log.debug(url)
    results = dict()

    try:
        req = Request(url, None)
        resp = urlopen(req, timeout=60).read()
        results = loads(resp)

    except Exception as e:
        logger.log.error("Error trying to search %s: %s" % (url, repr(e)))

    items = results.get('magnets', [])

    if len(items) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok("Magnetic", string(32075))
        del dialog

    else:
        window = DialogSelect("DialogSelectResults.xml", ADDON_PATH, "Default", title=string(32074) % query,
                              items=items)
        window.doModal()
        selection = window.ret
        del window
        if selection > -1:
            play(items[selection]['uri'])


def get_playable_link(page=''):
    """
    Get playable link from a web page
    :param page: URL address of the web page
    :type page: str
    :return: encode link to play video
    """
    page = normalize_string(page)
    exceptions_list = Storage.open("exceptions")
    result = page
    logger.log.debug(result)
    if 'divxatope' in page:
        page = page.replace('/descargar/', '/torrent/')
        result = page
    is_link = True
    logger.log.debug(exceptions_list.items())
    if exceptions_list.has(result):
        return page
    if page.startswith("http") and is_link:
        # exceptions
        logger.log.debug(result)
        # download page
        try:
            Browser.open(page)
            data = normalize_string(Browser.content)
            logger.log.debug(Browser.headers)
            if 'text/html' in Browser.headers.get("content-type", ""):
                content = re.findall('magnet:\?[^\'"\s<>\[\]]+', data)
                if content is not None and len(content) > 0:
                    result = content[0]
                else:
                    content = re.findall('/download\?token=[A-Za-z0-9%]+', data)
                    if content is not None and len(content) > 0:
                        result = Settings["url_address"] + content[0]
                    else:
                        content = re.findall('/telechargement/[a-z0-9-_.]+', data)  # cpasbien
                        if content is not None and len(content) > 0:
                            result = Settings["url_address"] + content[0]
                        else:
                            content = re.findall('/torrents/download/\?id=[a-z0-9-_.]+', data)  # t411
                            if content is not None and len(content) > 0:
                                result = Settings["url_address"] + content[0]
                            else:
                                content = re.findall('https?:[^\'"\s<>\[\]]+torrent', data)
                                if content is not None and len(content) > 0:
                                    result = content[0]
                                    result = result.replace('torcache.net', 'itorrents.org')
            else:
                exceptions_list.add(re.search("^https?://(.*?)/", page).group(1))
                exceptions_list.sync()
        except Exception as e:
            logger.log.error("Error getting playable link: %s" % repr(e))
            pass
    return quote_plus(result)
