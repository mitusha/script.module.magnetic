# coding: utf-8
# Name:        main.py
# Author:      Mancuniancol
# Created on:  28.11.2016
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Main Menu Magnetic
"""

import sys
from os import path
from re import findall
from urlparse import parse_qsl

import xbmcaddon
import xbmcgui
import xbmcplugin

import resources.lib.utils as utils
from resources.lib.play import search
from resources.lib.storage import *

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = dict(parse_qsl(sys.argv[2][1:]))

listing = []
speed_providers = Storage.open("speed")

mode = args.get('mode', None)
operation = args.get('search', None)
addonid = args.get('addonid', '')


# functions
def erase():
    """
    Erase cache with the providers information
    """
    Storage.open("providers").clear()


# Mode Menu
if operation:
    # contextual menu - Magnetizer
    xbmcplugin.endOfDirectory(addon_handle, True, False, False)
    search(info=args)

elif mode == 'provider':
    erase()
    xbmcaddon.Addon(addonid).openSettings()

elif mode == 'settings':
    erase()
    xbmcaddon.Addon().openSettings()

elif mode == 'clear_cache':
    erase()
    xbmcgui.Dialog().ok('Magnetic', 'Cache Cleared!')

elif mode == 'copy':
    erase()
    path_folder = xbmcaddon.Addon(addonid).getAddonInfo('path')
    value = dict()  # it contains all the settings from xml file
    fileName = path.join(path_folder, "resources", "settings.xml")
    if path.isfile(fileName):
        with open(fileName, 'r') as fp:
            data = fp.read()
        for key in findall('id="(\w+)"', data):
            if 'url' not in key and 'separator' not in key:
                value[key] = xbmcaddon.Addon(addonid).getSetting(id=key)

        items = []
        for provider in utils.get_list_providers():
            if provider['enabled']:
                items.append(provider['addonid'])
        items.remove(addonid)
        ret = xbmcgui.Dialog().select('Select the provider', ['All providers'] + items + ['CANCEL'])
        list_copy = (items if ret == 0 else [items[ret - 1]])
        if ret != -1 and ret <= len(items):
            for key, val in value.items():
                if not key.endswith('_search') and 'read_magnet_link' not in key:
                    for provider in list_copy:
                        xbmcaddon.Addon(provider).setSetting(id=key, value=val)
            xbmcgui.Dialog().ok('Magnetic', 'The %s settings were copied to \n%s' % (addonid, '\n'.join(list_copy)))


elif mode == 'check':
    speed_providers[addonid] = utils.check_provider(addonid)
    speed_providers.sync()
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'check_all':
    from xbmcgui import Dialog

    dialog = Dialog()
    for provider in utils.get_list_providers():
        if provider['enabled']:
            dialog.notification(provider['name'],
                                "Checking speed",
                                provider['thumbnail'], 10000)
            speed_providers[provider['addonid']] = utils.check_provider(provider['addonid'])
            speed_providers.sync()
    dialog.notification('Magnetic', 'Done!', time=50)
    del dialog
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'check_group':
    erase()
    message = utils.check_group_provider()
    xbmcgui.Dialog().ok('Magnetic', 'The enabled providers got %s' % message)

elif mode == 'enable':
    erase()
    utils.enable_provider(addonid)
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'disable':
    erase()
    utils.disable_provider(addonid)
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'enable_all':
    erase()
    for provider in utils.get_list_providers():
        utils.enable_provider(provider['addonid'])
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'disable_all':
    for provider in utils.get_list_providers():
        utils.disable_provider(provider['addonid'])
    xbmc.executebuiltin("Container.Refresh")

elif mode == 'defaults_all':
    import shutil
    import os.path

    erase()
    base_path = xbmc.translatePath('special://userdata/addon_data')
    for provider in utils.get_list_providers():
        folder = path.join(base_path, provider['addonid'])
        if os.path.isfile(folder):
            shutil.rmtree(folder)
    xbmcgui.Dialog().ok('Magnetic', 'Defaults settings applied')

if not mode:
    # creation menu
    for provider in utils.get_list_providers():
        name_provider = provider['name']  # gets name
        tag = '[B][COLOR FF008542][%s] [/COLOR][/B]' % utils.string(32090)
        menu_check = [(utils.string(32082), 'XBMC.RunPlugin(plugin://script.module.magnetic?mode=check&addonid=%s)' %
                       provider['addonid'])]
        menu_enable = (utils.string(32081), 'XBMC.RunPlugin(plugin://script.module.magnetic?mode=disable&addonid=%s)' %
                       provider['addonid'])

        if not provider['enabled']:
            tag = '[B][COLOR FFC40401][%s] [/COLOR][/B]' % utils.string(32091)
            menu_enable = (utils.string(32080),
                           'XBMC.RunPlugin(plugin://script.module.magnetic?mode=enable&addonid=%s)' %
                           provider['addonid'])
            menu_check = []
        speed = speed_providers.get(provider['addonid'], '')
        list_item = xbmcgui.ListItem(label=tag + name_provider + speed)
        icon = provider["thumbnail"]
        fanart = provider["fanart"]
        list_item.setArt({'thumb': icon,
                          'icon': icon,
                          'fanart': fanart})

        if provider['enabled']:
            url = base_url + '?mode=provider&addonid=%s' % provider['addonid']

        else:
            url = ''
        is_folder = False
        list_item.addContextMenuItems(menu_check +
                                      [(utils.string(32083),
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=check_all)'),
                                       (utils.string(32084),
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=check_group)'),
                                       menu_enable,
                                       (utils.string(32085),
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=enable_all)'),
                                       (utils.string(32086),
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=disable_all)'),
                                       (utils.string(32087),
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=copy&addonid=%s)' %
                                        provider['addonid']),
                                       (utils.string(32088),
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=defaults_all)'),
                                       (utils.string(32089),
                                        'XBMC.RunPlugin(plugin://script.module.magnetic?mode=settings)')],
                                      replaceItems=True)
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(addon_handle, listing, len(listing))
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(addon_handle, updateListing=True)

del speed_providers
