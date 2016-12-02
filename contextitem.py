# coding: utf-8

import sys
from urllib import quote_plus

import xbmc


def main():
    try:
        title = quote_plus(xbmc.getInfoLabel("ListItem.OriginalTitle"))
        if len(title) == 0:
            title = quote_plus(sys.listitem.getLabel())

        imdb_id = xbmc.getInfoLabel("ListItem.IMDBNumber")
        year = xbmc.getInfoLabel("ListItem.Year")
        tv_show_title = quote_plus(xbmc.getInfoLabel("ListItem.TVShowTitle"))
        season = xbmc.getInfoLabel("ListItem.Season")
        episode = xbmc.getInfoLabel("ListItem.Episode")

        # checking if it is tv show
        payload = '?search=general&title=%s' % title

        if len(tv_show_title) > 0 and len(season) > 0 and len(episode) > 0:
            payload = '?search=episode&title=%s&season=%s&episode=%s' % (tv_show_title, season, episode)

        elif len(tv_show_title) > 0 and len(season) > 0:
            payload = '?search=episode&title=%s&season=%s' % (tv_show_title, season)

        elif xbmc.getCondVisibility("Container.Content(movies)"):
            payload = '?search=movie&imdb=%s&title=%s&year=%s' % (imdb_id, title, year)

        # send the information to magnetic
        xbmc.executebuiltin("XBMC.RunPlugin(plugin://script.module.magnetic%s)" % payload)

    except Exception as e:
        print 'Error contextual menu Magnetizer: %s' % repr(e)


if __name__ == '__main__':
    main()
