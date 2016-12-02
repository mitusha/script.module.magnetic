# coding: utf-8

import sys

import xbmc


# noinspection PyBroadException
def main():
    try:
        query = xbmc.getInfoLabel("ListItem.OriginalTitle")
        if len(query) == 0:
            query = sys.listitem.getLabel()
        tv_show_title = xbmc.getInfoLabel("ListItem.TVShowTitle")
        season = xbmc.getInfoLabel("ListItem.Season")
        episode = xbmc.getInfoLabel("ListItem.Episode")
        # checking if it is tv show
        if len(tv_show_title) > 0 and len(season) > 0 and len(episode) > 0:
            query = "%s S%02dE%02d" % (tv_show_title, int(season), int(episode))
        elif len(tv_show_title) > 0 and len(season) > 0:
            query = "%s S%02d" % (tv_show_title, int(season))
        # send the information to magnetic
        if len(query) > 0:
            xbmc.executebuiltin("XBMC.RunPlugin(plugin://script.module.magnetic?mode=search&query=%s)" % query)
    except:
        pass


if __name__ == '__main__':
    main()
