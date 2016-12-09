# coding: utf-8

import sys
from urllib import quote_plus

import xbmc

from resources.lib.storage import Storage


def main():
    try:
        title = xbmc.getInfoLabel("ListItem.OriginalTitle")
        if len(title) == 0:
            title = sys.listitem.getLabel()
        imdb_id = xbmc.getInfoLabel("ListItem.IMDBNumber")
        year = xbmc.getInfoLabel("ListItem.Year")
        tv_show_title = xbmc.getInfoLabel("ListItem.TVShowTitle")
        season = xbmc.getInfoLabel("ListItem.Season")
        episode = xbmc.getInfoLabel("ListItem.Episode")

        # infoLabels
        info = {'Title': title,
                'Label': xbmc.getInfoLabel("ListItem.Title"),
                'Label2': xbmc.getInfoLabel("ListItem.Label2"),
                'OriginalTitle': xbmc.getInfoLabel("ListItem.OriginalTitle"),
                'Year': year,
                'code': imdb_id,
                'TVShowTitle': tv_show_title,
                'Episode': episode,
                'EpisodeName': xbmc.getInfoLabel("ListItem.EpisodeName"),
                'Season': season,
                'FileName': '',
                'DBTYPE': xbmc.getInfoLabel("ListItem.DBTYPE"),
                'DBID': xbmc.getInfoLabel("ListItem.DBID"),
                'Tag': xbmc.getInfoLabel("ListItem.Tag"),
                'Tagline': xbmc.getInfoLabel("ListItem.Tagline"),
                'PlotOutline': xbmc.getInfoLabel("ListItem.PlotOutline"),
                'Plot': xbmc.getInfoLabel("ListItem.Plot"),
                'Studio': xbmc.getInfoLabel("ListItem.Studio"),
                'Genre': xbmc.getInfoLabel("ListItem.Genre"),
                'Director': xbmc.getInfoLabel("ListItem.Director"),
                'Writer': xbmc.getInfoLabel("ListItem.Writer"),
                'Country': xbmc.getInfoLabel("ListItem.Country"),
                'Trailer': xbmc.getInfoLabel("ListItem.Trailer"),
                'Thumb': xbmc.getInfoLabel("ListItem.Thumb"),
                'Icon': xbmc.getInfoLabel("ListItem.Icon"),
                'UserRating': xbmc.getInfoLabel("ListItem.UserRating"),
                'Mpaa': xbmc.getInfoLabel("ListItem.Mpaa")
                }

        payload = '?search=general&title=%s' % quote_plus(title)

        if len(tv_show_title) > 0 and len(season) > 0 and len(episode) > 0:
            info['Title'] = info['Label'] = tv_show_title
            payload = '?search=episode&title=%s&season=%s&episode=%s' % (quote_plus(tv_show_title), season, episode)

        elif len(tv_show_title) > 0 and len(season) > 0:
            info['Title'] = info['Label'] = tv_show_title
            payload = '?search=episode&title=%s&season=%s' % (quote_plus(tv_show_title), season)

        elif xbmc.getCondVisibility("Container.Content(movies)"):
            payload = '?search=movie&imdb=%s&title=%s&year=%s' % (imdb_id, quote_plus(title), year)

        # save the infolabels
        magnetizer = Storage.open("magnetizer")
        magnetizer['info'] = info
        magnetizer.close()

        # send the information to magnetic
        xbmc.executebuiltin("XBMC.RunPlugin(plugin://script.module.magnetic%s)" % payload)

    except Exception as e:
        print 'Error contextual menu Magnetizer: %s' % repr(e)


if __name__ == '__main__':
    main()
