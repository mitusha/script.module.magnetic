# coding: utf-8
# Name:        provider.py
# Author:      Mancuniancol
# Created on:  28.11.2016
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Magnetic module which manages the providers and requests
This code is based in provider.py from pulsar
https://github.com/steeve/plugin.video.pulsar
"""

import re
import sys
import urllib2
from os import path
from urllib import unquote_plus, quote_plus
from urlparse import urlparse

import xbmcaddon

from browser import Browser
from ehp import *
from storage import *
from utils import PROVIDER_SERVICE_HOST, PROVIDER_SERVICE_PORT
from utils import get_setting, get_int, get_float

# just for pycharm's sake
Html()


def register(search, search_movie, search_episode, search_season):
    """
    Register each method from provider
    :param search: general search method
    :type search: callable
    :param search_movie: movies search method
    :type search_movie: callable
    :param search_episode: tv shows and anime search method
    :type search_episode: callable
    :param search_season: by season search method
    :type search_season: callable
    """
    if len(sys.argv) < 4:
        xbmcaddon.Addon().openSettings()
        return
    query = json.loads(unquote_plus(sys.argv[3]))
    method = sys.argv[2]
    addonid = sys.argv[1]
    method = {
        "search": search,
        "search_movie": search_movie,
        "search_episode": search_episode,
        "search_season": search_season
    }.get(method)

    # post to service magnet results
    callback = "http://" + str(PROVIDER_SERVICE_HOST) + ":" + str(
        PROVIDER_SERVICE_PORT) + "/providers?addonid=%s" % str(addonid)
    try:
        results = list(method(query))
        results = json.dumps(results)

    except Exception as e:
        results = json.dumps([])
        logger.log.error("Addon threw error %s: %s" % (str(addonid), repr(e)))

    # POST request
    request_url = urllib2.Request(callback, results)
    urllib2.urlopen(request_url)


# find the name in different language
def translator(title=None, imdb_id=None, language=None, extra=True):
    """
    Translate title
    :param title: Title to translate
    :type title: str
    :param imdb_id: IMDB id from the title
    :type  imdb_id: str
    :param language: requested language for the translation
    :type language: str
    :param extra: extra information
    :type extra: bool
    :return: translated title
    """
    keywords = {'en': '', 'de': '', 'es': 'espa', 'fr': 'french', 'it': 'italian', 'pt': 'portug'}
    if imdb_id:
        url_themoviedb = "http://api.themoviedb.org/3/find/%s?api_key=8d0e4dca86c779f4157fc2c469c372ca&language=%s" \
                         "&external_source=imdb_id" % (imdb_id, language)
        if Browser.open(url_themoviedb):
            results = json.loads(Browser.content)
            if len(results['movie_results']) > 0:
                title = results['movie_results'][0]['title'].encode('utf-8')
                original_title = results['movie_results'][0]['original_title'].encode('utf-8')
            elif len(results['tv_results']) > 0:
                title = results['tv_results'][0]['name'].encode('utf-8')
                original_title = results['tv_results'][0]['original_name'].encode('utf-8')
            else:
                title = ""
                original_title = ""
            if title == original_title and extra:
                title += ' ' + keywords[language]
        else:
            title = 'Pas de communication avec le themoviedb.org'
    else:
        url_themoviedb = "http://api.themoviedb.org/3/search/tv?api_key=8d0e4dca86c779f4157fc2c469c372ca" \
                         "&query=%s&language=%s" % (title.replace(' ', '+'), language)
        if Browser.open(url_themoviedb):
            results = json.loads(Browser.content)
            if len(results['results']) > 0:
                title = results['results'][0]['name']
                original_title = results['results'][0]['original_name']
                if title == original_title and extra:
                    title += ' ' + keywords[language]
        else:
            title = 'Pas de communication avec le themoviedb.org'
    return Filtering.safe_name(title.rstrip())


#  Get the title from imdb id code
def imdb_title(imdb_id):
    """
    Get title from IMDB id
    :param imdb_id: IMDB id
    :type imdb_id: str
    :return: title
    """
    result = ''
    if Browser.open('http://www.omdbapi.com/?i=%s&r=json' % imdb_id):
        data = Browser.content.replace('"', '').replace('{', '').replace('}', '').split(',')
        result = data[0].split(":")[1] + ' ' + data[1].split(":")[1]
    return result


def clean_size(text=""):
    """
    Remove unnecessary information from string which has size information ex: 6.50GB
    :param text:
    :return: cleaned string
    """
    if text is not None:
        pos = text.rfind('B')
        if pos > 0:
            text = text[:pos] + 'B'
    return text


def add_base_url(url=''):
    """
    Create a full URL
    :param url: url address
    :type url: str
    :return: full URL
    """
    if url.startswith('//'):
        url = 'http:' + url
    elif url.startswith('/'):
        if Settings.url.endswith('/'):
            url = Settings.url + url[1:]
        else:
            url = Settings.url + url
    elif not url.startswith('http') and not url.startswith('magnet:'):
        url = Settings.url + '/' + url
    return url


def clean_magnet(magnet="", info_hash=""):
    """
    Create a magnet from info_hash if it doesn't exist
    :param magnet: magnet or torrent
    :type magnet: str
    :param info_hash: info_hash
    :type info_hash: str
    :return: complete magnet or torrent
    """
    if len(magnet) > 0:
        magnet = add_base_url(magnet)
    elif len(magnet) == 0 and len(info_hash) > 0:
        magnet = 'magnet:?xt=urn:btih:%s' % info_hash
    return magnet


def parse_json(data):
    """
    Createa json from string
    :param data: json in string format
    :type data: str
    :return: json
    """
    return json.loads(data)


def exception(title=None):
    """
    Change the title to the standard name in the torrent sites
    :param title: title to check
    :type title: str
    :return: the new title
    """
    if title:
        title = title.lower()
        title = title.replace('csi crime scene investigation', 'CSI')
        title = title.replace('law and order special victims unit', 'law and order svu')
        title = title.replace('law order special victims unit', 'law and order svu')
    return title


def read_keywords(keywords):
    """
    Create list from string where the values are marked between curly brackets {example}
    :param keywords: string with the information
    :type keywords: str
    :return: list with collected keywords
    """
    results = []
    for value in re.findall('{(.*?)}', keywords):
        results.append(value)
    return results


def format_decimal(times):
    """
    Format a number to decimal
    :param times: value
    :type  times: int
    :return: string  with the formatted value
    """
    value = ''
    for i in range(1, times):
        value += '0'
    return "%" + value + "%sd" % times


class MetaSettings(type):
    """
    Class to read values from add-on's settings
    """

    @classmethod
    def __getitem__(mcs, item):
        if item is "max_magnets":
            return get_int(mcs.value.get(item, "10"))
        elif item is "separator":
            return mcs.value.get(item, "%20")
        elif item is "notification":
            return get_int(mcs.value.get(item, "50"))
        elif item.endswith("accept"):
            temp = mcs.value.get(item, "{*}")
            return "{*}" if temp is "" else temp
        elif item.endswith("max_size"):
            return get_float(mcs.value.get(item, "10"))
        elif item.endswith("min_size"):
            return get_float(mcs.value.get(item, "0"))
        elif item.endswith("_title"):
            return mcs.value.get(item, "true")
        elif item.endswith("read_magnet_link"):
            return mcs.value.get(item, "false")
        else:
            return mcs.value.get(item, "")

    # General information
    id_addon = xbmcaddon.Addon().getAddonInfo('ID')  # gets name
    icon = xbmcaddon.Addon().getAddonInfo('icon')
    fanart = xbmcaddon.Addon().getAddonInfo('fanart')
    path_folder = xbmcaddon.Addon().getAddonInfo('path')
    name = xbmcaddon.Addon().getAddonInfo('name')  # gets name
    name_provider = re.sub('.COLOR (.*?)]', '', name.replace('[/COLOR]', ''))
    value = {}  # it contains all the settings from xml file
    file_name = path.join(path_folder, "resources", "settings.xml")
    if path.isfile(file_name):
        with open(file_name, 'r') as fp:
            data = fp.read()
        for key in re.findall('id="(\w+)"', data):
            value[key] = get_setting(key)  # reading the values from xbmcaddon.Addon().xml
    temp = urlparse(value.get('general_url', ""))
    url = '%s://%s' % (temp.scheme, temp.netloc)


class Settings(object):
    """
    User's class to get the values from the add-on's settings
    """

    def __init__(self):
        pass

    __metaclass__ = MetaSettings
    pass


class Filtering:
    """
    Helper to filtering titles
    """

    def __init__(self):
        pass

    info = dict(title="")
    post_data = {}
    get_data = None
    reason = ''
    title = ''
    results = []
    url = ''
    filter_title = 'true'
    quality_allow = read_keywords(Settings["general_accept"])
    quality_deny = read_keywords(Settings["general_block"])
    min_size = Settings["general_min_size"]
    max_size = Settings["general_max_size"]
    queries = [Settings["general_query1"],
               Settings["general_query2"],
               Settings["general_query3"],
               Settings["general_query4"],
               Settings["general_query5"]]

    @classmethod
    def use_general(cls, info):
        """
        Set the values for general search
        :param info: payload
        :type info: dict
        :return:
        """
        cls.info = info
        cls.url = Settings["general_url"]
        cls.filter_title = Settings["general_title"]
        cls.quality_allow = read_keywords(Settings["general_accept"])
        cls.quality_deny = read_keywords(Settings["general_block"])
        cls.min_size = Settings["general_min_size"]
        cls.max_size = Settings["general_max_size"]
        cls.queries = [Settings["general_query1"],
                       Settings["general_query2"],
                       Settings["general_query3"],
                       Settings["general_query4"],
                       Settings["general_query5"]]

    @classmethod
    def use_movie(cls, info):
        """
        Set the values for movies search
        :param info: payload
        :type info: dict
        :return:
        """
        cls.info = info
        cls.url = Settings["movie_url"]
        cls.filter_title = Settings["movie_title"]
        cls.quality_allow = read_keywords(Settings["movie_accept"])
        cls.quality_deny = read_keywords(Settings["movie_block"])
        cls.min_size = Settings["movie_min_size"]
        cls.max_size = Settings["movie_max_size"]
        cls.queries = [Settings["movie_query1"],
                       Settings["movie_query2"],
                       Settings["movie_query3"],
                       Settings["movie_query4"],
                       Settings["movie_query5"]]

    @classmethod
    def use_tv(cls, info):
        """
        Set the values for TV Shows search
        :param info: payload
        :type info: dict
        :return:
        """
        cls.info = info
        cls.url = Settings["tv_url"]
        cls.filter_title = Settings["tv_title"]
        cls.quality_allow = read_keywords(Settings["tv_accept"])
        cls.quality_deny = read_keywords(Settings["tv_block"])
        cls.min_size = Settings["tv_min_size"]
        cls.max_size = Settings["tv_max_size"]
        cls.queries = [Settings["tv_query1"],
                       Settings["tv_query2"],
                       Settings["tv_query3"],
                       Settings["tv_query4"],
                       Settings["tv_query5"]]

    @classmethod
    def use_season(cls, info):
        """
        Set the values for by season search
        :param info: payload
        :type info: dict
        :return:
        """
        cls.info = info
        cls.url = Settings["season_url"]
        cls.filter_title = Settings["season_title"]
        cls.quality_allow = read_keywords(Settings["season_accept"])
        cls.quality_deny = read_keywords(Settings["season_block"])
        cls.min_size = Settings["season_min_size"]
        cls.max_size = Settings["season_max_size"]
        cls.queries = [Settings["season_query1"],
                       Settings["season_query2"],
                       Settings["season_query3"],
                       Settings["season_query4"],
                       Settings["season_query5"]]

    @classmethod
    def use_anime(cls, info):
        """
        Set the values for anime search
        :param info: payload
        :type info: dict
        :return:
        """
        cls.info = info
        cls.url = Settings["anime_url"]
        cls.filter_title = Settings["anime_title"]
        cls.quality_allow = read_keywords(Settings["anime_accept"])
        cls.quality_deny = read_keywords(Settings["anime_block"])
        cls.min_size = Settings["anime_min_size"]
        cls.max_size = Settings["anime_max_size"]
        cls.queries = [Settings["anime_query1"],
                       Settings["anime_query2"],
                       Settings["anime_query3"],
                       Settings["anime_query4"],
                       Settings["anime_query5"]]

    @classmethod
    def information(cls):
        """
        Print the information about the filtering
        """
        logger.log.debug('Accepted Keywords: %s' % cls.quality_allow)
        logger.log.debug('Blocked Keywords: %s' % cls.quality_deny)
        logger.log.debug('min Size: %s' % str(cls.min_size) + ' GB')
        logger.log.debug('max Size: %s' % ((str(cls.max_size) + ' GB') if cls.max_size != 10 else 'MAX'))

    @staticmethod
    def included(value, keys, strict=False):
        """
        Check if the keys are present in the string
        :param value: string to test
        :type value: str
        :param keys: values to check
        :type keys: list
        :param strict: if it accepts partial results
        :type strict: bool
        :return: True is any key is included. False, otherwise.
        """
        value = ' ' + value + ' '
        if '*' in keys:
            res = True
        else:
            res1 = []
            for key in keys:
                res2 = []
                for item in re.split('\s', key):
                    item = item.replace('?', ' ').replace('_', ' ')
                    if strict:
                        item = ' ' + item + ' '  # it makes that strict the comparation
                    if item.upper() in value.upper():
                        res2.append(True)
                    else:
                        res2.append(False)
                res1.append(all(res2))
            res = any(res1)
        return res

    @classmethod
    def size_clearance(cls, size):
        """
        Convert string with size format to number ex: 1kb = 1000
        :param size: string with the size format
        :type size: str
        :return: converter value in integer
        """
        max_size1 = 100 if cls.max_size == 10 else cls.max_size
        res = False
        value = get_float(size)
        value *= 0.001 if 'M' in size else 1
        if cls.min_size <= value <= max_size1:
            res = True
        return res

    # noinspection PyBroadException
    @staticmethod
    def normalize_string(name=None):
        """
        Convert any type of string to latin-1 encoding
        :param name: string to convert
        :type name: str
        :return: converter string
        """
        if name:
            from unicodedata import normalize
            import types
            try:
                normalize_name = name.decode('unicode-escape').encode('latin-1')
            except:
                if types.StringType == type(name):
                    unicode_name = unicode(name, 'utf-8', 'ignore')
                else:
                    unicode_name = name
                normalize_name = normalize('NFKD', unicode_name).encode('ascii', 'ignore')
            return normalize_name
        return ''

    @staticmethod
    def un_code_name(name):
        """
        Convert all the &# codes to char, remove extra-space and normalize
        :param name: string to convert
        :type name: str
        :return: converted string
        """
        from HTMLParser import HTMLParser

        name = name.replace('<![CDATA[', '').replace(']]', '')
        name = HTMLParser().unescape(name.lower())
        return name

    @staticmethod
    def unquote_name(name):
        """
        Convert all %symbols to char
        :param name: string to convert
        :type name: str
        :return: converted string
        """
        from urllib import unquote

        return unquote(name)

    @classmethod
    def safe_name(cls, value):
        """
        Make the name directory and filename safe
        :param value: string to convert
        :type value: str
        :return: converted string
        """
        value = cls.normalize_string(value)  # First normalization
        value = cls.unquote_name(value)
        value = cls.un_code_name(value)
        value = cls.normalize_string(
            value)  # Last normalization, because some unicode char could appear from the previous steps
        value = value.lower().title()
        keys = {'"': ' ', '*': ' ', '/': ' ', ':': ' ', '<': ' ', '>': ' ', '?': ' ', '|': ' ', '_': ' ',
                "'": '', 'Of': 'of', 'De': 'de', '.': ' ', ')': ' ', '(': ' ', '[': ' ', ']': ' ', '-': ' '}
        for key in keys.keys():
            value = value.replace(key, keys[key])
        value = ' '.join(value.split())
        return value.replace('S H I E L D', 'SHIELD')

    @classmethod
    def verify(cls, name, size):
        """
        Check the name matches with the title and the filtering keywords, and the size with filtering size values
        :param name: name of the torrent
        :type name: str
        :param size: size of the torrent
        :type size: str
        :return: True is complied with the filtering.  False, otherwise.
        """
        if name is None or name is '':
            cls.reason = name.replace(' - ' + Settings.name_provider, '') + ' ***Empty Name***'
            return False
        name = cls.safe_name(name)
        cls.title = cls.safe_name(cls.title) if cls.filter_title in 'true' else name
        normalized_title = cls.normalize_string(cls.title)  # because sometimes there are missing accents in the results
        cls.reason = name.replace(' - ' + Settings.name_provider, '') + ' ***Blocked File by'
        list_to_verify = [cls.title, normalized_title] if cls.title != normalized_title else [cls.title]
        if cls.included(name, list_to_verify, True):
            result = True
            if name is not None:
                if not cls.included(name, cls.quality_allow):
                    cls.reason += ", Missing Accepted Keyword"
                    result = False
                if cls.included(name, cls.quality_deny):
                    cls.reason += ", Blocked Keyword"
                    result = False
            if size is not None and size is not '':
                if not cls.size_clearance(size):
                    result = False
                    cls.reason += ", Size"
        else:
            result = False
            cls.reason += ", Name"
        cls.reason = cls.reason.replace('by,', 'by') + '***'
        return result


def generate_payload(generator=None, verify_name=True, verify_size=True):
    """
    Create the payload from the generator method from the provider
    :param generator: generator method
    :type generator: callable
    :param verify_name: if the name needs to be verified
    :type verify_name: bool
    :param verify_size: if the size needs to be verified
    :type verify_size: bool
    :return: magnets and torrent results
    """
    Filtering.information()  # print filters xbmcaddon.Addon()
    results = []
    cont = 0
    for name, info_hash, uri, size, seeds, peers in generator:
        size = clean_size(size)
        uri = clean_magnet(uri, info_hash)
        v_name = name if verify_name else Filtering.title
        v_size = size if verify_size else None
        logger.log.debug("name: %s \n info_hash: %s\n magnet: %s\n size: %s\n seeds: %s\n peers: %s" % (
            name, info_hash, uri, size, seeds, peers))
        if Filtering.verify(v_name, v_size):
            cont += 1
            if Settings["read_magnet_link"] == "true":
                magnetic_url = "http://%s:%s/" % (str(PROVIDER_SERVICE_HOST), str(PROVIDER_SERVICE_PORT))
                uri = "%s?uri=%s" % (magnetic_url, quote_plus(uri))  # magnet
            results.append({"name": name,
                            "uri": uri,
                            "info_hash": info_hash,
                            "size": size,
                            "seeds": get_int(seeds),
                            "peers": get_int(peers),
                            "language": Settings["language"],
                            "provider": Settings.name,
                            "icon": Settings.icon,
                            })  # return the torrent
            if cont >= Settings["max_magnets"]:  # limit magnets
                break
        else:
            logger.log.debug(Filtering.reason)
    logger.log.debug('>>>>>>' + str(cont) + ' torrents sent to Magnetic<<<<<<<')
    return results


def process(generator=None, verify_name=True, verify_size=True):
    """
    Create a thread for each generator
    :param generator: generator method
    :type generator: callable
    :param verify_name: if the name needs to be verified
    :type verify_name: bool
    :param verify_size: if the size needs to be verified
    :type verify_size: bool
    :return: magnets and torrent results from all threads
    """
    from threading import Thread
    threads = []

    t = Thread(target=execute_process, args=(generator, verify_name, verify_size))
    threads.append(t)

    # Start all threads
    for x in threads:
        x.start()

    # Wait for all of them to finish
    for x in threads:
        x.join()

    return Filtering.results


def execute_process(generator=None, verify_name=True, verify_size=True):
    """
    Process all the queries from the provider and add the result to Filtering static class
    :param generator: generator method
    :type generator: callable
    :param verify_name: if the name needs to be verified
    :type verify_name: bool
    :param verify_size: if the size needs to be verified
    :type verify_size: bool
    """
    # get the cloudhole key
    if Settings["use_cloudhole"] == 'true':
        Browser.clearance = xbmcaddon.Addon('script.module.magnetic').getSetting('clearance')
        Browser.user_agent = xbmcaddon.Addon('script.module.magnetic').getSetting('user_agent')

        # start the process
    for query in Filtering.queries:
        keywords = read_keywords(query)

        for keyword in keywords:
            keyword = keyword.lower()
            if 'title' in keyword:
                if ':' in keyword:
                    keys = keyword.split(':')
                    logger.log.debug(Filtering.info)
                    title = translator(Filtering.info['title'], Filtering.info.get('imdb_id', ''), keys[1], False)
                else:
                    title = Filtering.info["title"].encode('utf-8')
                query = query.replace('{%s}' % keyword, title)

            if 'year' in keyword:
                query = query.replace('{%s}' % keyword, Filtering.info["year"])

            if 'season' in keyword:
                if ':' in keyword:
                    keys = keyword.split(':')
                    season = format_decimal(get_int(keys[1])) % Filtering.info["season"]
                else:
                    season = '%s' % Filtering.info["season"]
                query = query.replace('{%s}' % keyword, '' + season)

            if 'episode' in keyword:
                if ':' in keyword:
                    keys = keyword.split(':')
                    episode = format_decimal(get_int(keys[1])) % Filtering.info["episode"]
                else:
                    episode = '%s' % Filtering.info["episode"]
                query = query.replace('{%s}' % keyword, '' + episode)

        if query is not '':
            # creating url
            url_search = Filtering.url.replace('QUERY', query.replace(' ', Settings['separator']))

            # creating the payload for Post Method
            payload = dict()

            for key, value in Filtering.post_data.iteritems():
                if 'QUERY' in value:
                    payload[key] = Filtering.post_data[key].replace('QUERY', query)

                else:
                    payload[key] = Filtering.post_data[key]

            logger.log.debug(query)
            logger.log.debug(Filtering.post_data)
            logger.log.debug(payload)

            # creating the payload for Get Method
            data = None
            if Filtering.get_data is not None:
                data = dict()

                for key, value in Filtering.get_data.iteritems():
                    if 'QUERY' in value:
                        data[key] = Filtering.get_data[key].replace('QUERY', query)

                    else:
                        data[key] = Filtering.get_data[key]

            # to do filtering by name
            Filtering.title = query
            logger.log.debug(url_search)

            # requesting the QUERY and adding info
            Browser.open(url_search, post_data=payload, get_data=data)
            Filtering.results.extend(generate_payload(generator(Browser.content), verify_name, verify_size))
