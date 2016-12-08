# coding: utf-8
# Name:        utils.py
# Author:      Mancuniancol
# Created on:  28.11.2016
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Helper methods
"""

import os
import re
from json import loads
from urllib2 import Request, urlopen

import xbmc
import xbmcaddon
import xbmcgui

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_ICON = ADDON.getAddonInfo("icon")
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_PATH = ADDON.getAddonInfo("path")
ADDON_VERSION = ADDON.getAddonInfo("version")
PATH_ADDONS = xbmc.translatePath("special://home/addons/")
PATH_TEMP = xbmc.translatePath("special://temp")
# provider service config
PROVIDER_SERVICE_HOST = "127.0.0.1"
PROVIDER_SERVICE_PORT = 5005


def check_provider(provider=""):
    """
    Verify the provider's health
    :param provider: name of provider to check
    :type provider: str
    :return: string with the duration and number of collected results
    """
    magnetic_url = "http://%s:%s" % (str(PROVIDER_SERVICE_HOST), str(PROVIDER_SERVICE_PORT))
    title = 'simpsons'
    if 'nyaa' in provider:
        title = 'one%20piece'
    if 'yts' in provider:
        title = 'batman%201989'
    url = magnetic_url + "?search=general&title=%s&provider=%s" % (title, provider)
    results = dict()
    try:
        req = Request(url, None)
        resp = urlopen(req).read()
        results = loads(resp)
    except Exception as e:
        print "Error checking provider %s: %s" % (provider, repr(e))
        pass
    duration = results.get('duration', '[COLOR FFC40401]Error[/COLOR]')
    items = results.get('results', 'zero')
    return " [%s for %s items]" % (duration, items)


def check_group_provider():
    """
    Verify the health of enabled providers
    """
    magnetic_url = "http://%s:%s" % (str(PROVIDER_SERVICE_HOST), str(PROVIDER_SERVICE_PORT))
    title = '12%20monkeys'
    url = magnetic_url + "?search=general&title=%s" % title
    results = dict()
    try:
        req = Request(url, None)
        resp = urlopen(req).read()
        results = loads(resp)
    except Exception as e:
        print "Error checking enabled providers: %s" % (repr(e))
        pass
    duration = results.get('duration', '[COLOR FFC40401]Error[/COLOR]')
    items = results.get('results', 'zero')
    return " [%s for %s items]" % (duration, items)


def get_list_providers():
    """
    Get the list of installed providers
    :return: list of installed providers
    """
    results = []
    list_providers = loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", '
                                               '"method": "Addons.GetAddons", '
                                               '"id": 1, '
                                               '"params": {"type" : "xbmc.python.script", '
                                               '"properties": ["enabled", "name", "thumbnail", "fanart"]}}'))
    for one_provider in list_providers["result"]["addons"]:
        if one_provider['addonid'].startswith('script.magnetic.'):
            results.append(one_provider)
    return results


def get_list_providers_enabled():
    """
    Get the list of enabled providers
    :return: list of enable providers
    """

    results = []
    list_providers = loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", '
                                               '"method": "Addons.GetAddons", '
                                               '"id": 1, '
                                               '"params": {"type" : "xbmc.python.script", '
                                               '"properties": ["enabled", "name"]}}'))
    for one_provider in list_providers["result"]["addons"]:
        if one_provider['addonid'].startswith('script.magnetic.') and one_provider['enabled']:
            results.append(one_provider['addonid'])
    return results


def disable_provider(provider):
    """
    Disable a specific provider
    :param provider: provider to disable
    :type provider: str
    """
    xbmc.executeJSONRPC('{"jsonrpc":"2.0",'
                        '"method":"Addons.SetAddonEnabled",'
                        '"id":1,"params":{"addonid":"%s","enabled":false}}' % provider)


def enable_provider(provider):
    """
    Enable a specific provider
    :param provider: provider to enable
    :type provider: str
    """
    xbmc.executeJSONRPC('{"jsonrpc":"2.0",'
                        '"method":"Addons.SetAddonEnabled",'
                        '"id":1,"params":{"addonid":"%s","enabled":true}}' % provider)


def get_setting(key, converter=str, choices=None):
    """
    Read add-on's settings
    # Borrowed from xbmc swift2
    :param key: parameter to read
    :type key: str
    :param converter: type of parameter
    :type converter: object
    :param choices: if the parameter has different values, it could pick one
    :type choices: object
    :return:
    """
    value = ADDON.getSetting(id=key)
    if converter is str:
        return value
    elif converter is unicode:
        return value.decode('utf-8')
    elif converter is bool:
        return value == 'true'
    elif converter is int:
        return int(value)
    elif isinstance(choices, (list, tuple)):
        return choices[int(value)]
    else:
        raise TypeError('Acceptable converters are str, unicode, bool and '
                        'int. Acceptable choices are instances of list '
                        ' or tuple.')


def set_setting(key, value):
    """
    Modify add-on's settings
    :param key: parameter to modify
    :type key: str
    :param value: value of the parameter
    :type value: str
    """
    ADDON.setSetting(key, value)


def get_icon_path():
    """
    Get the path from add-on's icon
    :return: icon's path
    """
    addon_path = xbmcaddon.Addon().getAddonInfo("path")
    return os.path.join(addon_path, 'icon.png')


def string(id_value):
    """
    Internationalisation string
    :param id_value: id value from string.po file
    :type id_value: int
    :return: the translated string
    """
    return xbmcaddon.Addon().getLocalizedString(id_value)


def get_int(text):
    """
    Convert string to integer number
    :param text: string to convert
    :type text: str
    :return: converted string in integer
    """
    return int(get_float(text))


def get_float(text):
    """
    Convert string to float number
    :param text: string to convert
    :type text: str
    :return: converted string in float
    """
    value = 0
    if isinstance(text, (float, long, int)):
        value = float(text)
    elif isinstance(text, str):
        # noinspection PyBroadException
        try:
            text = clean_number(text)
            match = re.search('([0-9]*\.[0-9]+|[0-9]+)', text)
            if match:
                value = float(match.group(0))
        except:
            value = 0
    return value


# noinspection PyBroadException
def size_int(size_txt):
    """
    Convert string with size format to integer
    :param size_txt: string to be converted
    :type size_txt: str
    :return: converted string in integer
    """
    try:
        return int(size_txt)
    except:
        size_txt = size_txt.upper()
        size1 = size_txt.replace('B', '').replace('I', '').replace('K', '').replace('M', '').replace('G', '')
        size = get_float(size1)
        if 'K' in size_txt:
            size *= 1000
        if 'M' in size_txt:
            size *= 1000000
        if 'G' in size_txt:
            size *= 1e9
        return size


def clean_number(text):
    """
    Convert string with a number to USA decimal format
    :param text: string with the number
    :type text: str
    :return: converted number in string
    """
    comma = text.find(',')
    point = text.find('.')
    if comma > 0 and point > 0:
        if comma < point:
            text = text.replace(',', '')
        else:
            text = text.replace('.', '')
            text = text.replace(',', '.')
    return text


def notify(message, image=None):
    """
    Create notification dialog
    :param message: message to notify
    :type message: str
    :param image: path of the image
    :type image: str
    """
    dialog = xbmcgui.Dialog()
    dialog.notification(ADDON_NAME, message, icon=image)
    del dialog


def display_message_cache():
    """
    Create the progress dialog when the cache is used
    """
    p_dialog = xbmcgui.DialogProgressBG()
    p_dialog.create('Magnetic Manager', string(32061))
    xbmc.sleep(250)
    p_dialog.update(25, string(32065))
    xbmc.sleep(250)
    p_dialog.update(50, string(32065))
    xbmc.sleep(250)
    p_dialog.update(75, string(32065))
    xbmc.sleep(250)
    p_dialog.close()
    del p_dialog
