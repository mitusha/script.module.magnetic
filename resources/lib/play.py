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
        window = DialogSelect("DialogSelectLarge.xml", ADDON_PATH, "Default", title=string(32074) % query, items=items)
        window.doModal()
        selection = window.ret
        del window
        if selection > -1:
            play(items[selection]['uri'])
