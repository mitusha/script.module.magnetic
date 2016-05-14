# -*- coding: utf-8 -*-
# This code is based in provider.py from pulsar
# https://github.com/steeve/plugin.video.pulsar

import json
import re
import sys
import urllib2
from cookielib import CookieJar, LWPCookieJar
from os import path
from urllib import unquote_plus, urlencode, quote

import xbmcaddon
import xbmcgui

from ehp import *
from logger import log
from magnetic import PROVIDER_SERVICE_HOST, PROVIDER_SERVICE_PORT
from utils import ADDON

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36" \
             " (KHTML, like Gecko) Chrome/30.0.1599.66 Safari/537.36"
Html()
COOKIES = CookieJar()
urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(COOKIES)))

season_names = {'en': 'season',
                'es': 'temporada',
                'fr': 'saison',
                'nl': 'seizoen',
                'ru': 'сезон',
                'it': 'stagione',
                'de': 'saison',
                'pt': 'temporada',
                }


# noinspection PyBroadException
def register(search, search_movie, search_episode, search_season):
    query = json.loads(unquote_plus(sys.argv[3]))
    method = sys.argv[2]
    addonid = sys.argv[1]
    method = {
        "search": search,
        "search_movie": search_movie,
        "search_episode": search_episode,
        "search_season": search_season,
    }.get(method)

    # post to service magnet results
    callback = "http://" + str(PROVIDER_SERVICE_HOST) + ":" + str(
        PROVIDER_SERVICE_PORT) + "/providers?addonid=%s" % str(addonid)
    try:
        results = list(method(query))
        results = json.dumps(results)

    except:
        results = json.dumps([])
        log.error("Addon threw error:" + str(addonid))

    request_url = urllib2.Request(callback, results)
    urllib2.urlopen(request_url, timeout=60)


class closing(object):
    def __init__(self, thing):
        self.thing = thing

    def __enter__(self):
        return self.thing

    def __exit__(self):
        self.thing.close()


def parse_json(data):
    import json
    return json.loads(data)


def parse_xml(data):
    import xml.etree.ElementTree as eT
    return eT.fromstring(data)


def request(url, params=None, headers=None, data=None, method=None):
    if headers is None:
        headers = {}
    if params is None:
        params = {}
    if params:
        url = "".join([url, "?", urlencode(params)])

    req = urllib2.Request(url)
    if method:
        req.get_method = lambda: method
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept-Encoding", "gzip")
    for k, v in headers.items():
        req.add_header(k, v)
    if data:
        req.add_data(data)
    try:
        with closing(urllib2.urlopen(req)) as response:
            data = response.read()
            if response.headers.get("Content-Encoding", "") == "gzip":
                import zlib
                data = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(data)
            response.data = data
            response.json = lambda: parse_json(data)
            response.xml = lambda: parse_xml(data)
            return response
    except urllib2.HTTPError, e:
        log.error("http error: %s => %d %s" % (url, e.code, e.reason))
        return None, None


# Borrowed from xbmcswift2
def get_setting(key, converter=str, choices=None):
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


def HEAD(*args, **kwargs):
    return request(*args, method="HEAD", **kwargs)


def GET(*args, **kwargs):
    return request(*args, method="GET", **kwargs)


def POST(*args, **kwargs):
    return request(*args, method="POST", **kwargs)


def PUT(*args, **kwargs):
    return request(*args, method="PUT", **kwargs)


def DELETE(*args, **kwargs):
    return request(*args, method="DELETE", **kwargs)


# provider web browser with cookies management
class Browser:
    def __init__(self):
        pass

    _cookies = None
    cookies = LWPCookieJar()
    content = None
    status = None

    @classmethod
    def create_cookies(cls, payload):

        cls._cookies = urlencode(payload)

    # to open any web page
    @classmethod
    def open(cls, url='', language='en', payload=None):
        if payload is None:
            payload = {}

        log.info(url)
        result = True
        if len(payload) > 0:
            cls.create_cookies(payload)
        if cls._cookies is not None:
            req = urllib2.Request(url, cls._cookies)
            cls._cookies = None
        else:
            req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        req.add_header('Content-Language', language)
        req.add_header("Accept-Encoding", "gzip")
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cls.cookies))  # open cookie jar
        try:
            response = opener.open(req)  # send cookies and open url
            # borrow from provider.py Steeve
            if response.headers.get("Content-Encoding", "") == "gzip":
                import zlib
                cls.content = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(response.read())
            else:
                cls.content = response.read()
            response.close()
            cls.status = 200
        except urllib2.HTTPError as e:
            cls.status = e.code
            result = False
        except urllib2.URLError as e:
            cls.status = e.reason
            result = False
        return result

    # alternative when it is problem with https
    @classmethod
    def open2(cls, url=''):
        import httplib

        word = url.split("://")
        pos = word[1].find("/")
        conn = httplib.HTTPConnection(re.search[:pos])
        conn.request("GET", re.search[pos:])
        r1 = conn.getresponse()
        cls.status = str(r1.status) + " " + r1.reason
        cls.content = r1.read()
        if r1.status == 200:
            return True
        else:
            return False

    # used for sites with login
    @classmethod
    def login(cls, url, payload, word):
        result = False
        cls.create_cookies(payload)
        if cls.open(url):
            result = True
            data = cls.content
            if word in data:
                cls.status = 'Wrong Username or Password'
                result = False
        return result


# find the name in different language
def translator(imdb_id, language, extra=True):
    import json
    keywords = {'en': '', 'de': '', 'es': 'espa', 'fr': 'french', 'it': 'italian', 'pt': 'portug'}
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
    return title.rstrip()


#  Get the title from imdb id code
def imdb_title(imdb_id):
    result = ''
    if Browser.open('http://www.omdbapi.com/?i=%s&r=json' % imdb_id):
        data = Browser.content.replace('"', '').replace('{', '').replace('}', '').split(',')
        result = data[0].split(":")[1] + ' ' + data[1].split(":")[1]
    return result


# get the first magnet or torrent from one webpage
def get_links(page):
    if page is None:
        result = ''
    else:
        if page[:1] is '/':
            page = Settings.value["url_address"] + page
        browser = Browser()
        result = ""
        if browser.open(quote(page).replace("%3A", ":")):
            content = re.findall('magnet:\?[^\'"\s<>\[\]]+', browser.content)
            if content is not None and len(content) > 0:
                result = content[0]
            else:
                content = re.findall('http(.*?).torrent', browser.content)
                if content is not None and len(content) > 0:
                    result = 'http' + content[0] + '.torrent'
    return result


def size_int(size_txt):
    size_txt = size_txt.upper()
    size1 = size_txt.replace('B', '').replace('I', '').replace('K', '').replace('M', '').replace('G', '')
    size = get_float(size1)
    if 'K' in size_txt:
        size *= 1000
    if 'M' in size_txt:
        size *= 1000000
    if 'G' in size_txt:
        size *= 1e9
    return get_int(size)


def get_int(text):
    # noinspection PyBroadException
    try:
        value = int(re.search('([0-9]*\.[0-9]+|[0-9]+)', text).group(0))
    except:
        value = 0
    return value


def get_float(text):
    # noinspection PyBroadException
    try:
        value = float(re.search('([0-9]*\.[0-9]+|[0-9]+)', text).group(0))
    except:
        value = 0
    return value


def exception(title):
    title = title.lower()
    title = title.replace('csi crime scene investigation', 'CSI')
    title = title.replace('law and order special victims unit', 'law and order svu')
    title = title.replace('law order special victims unit', 'law and order svu')
    return title


# read provider xbmcaddon.Addon()
class MetaSettings(type):
    @classmethod
    def __getitem__(mcs, item):
        if item is "max_magnets":
            return int(mcs.value.get(item, "10"))
        elif item is "language":
            return mcs.value.get(item, "en")
        elif item is "episodes":
            return mcs.value.get("episodes", "false")
        else:
            return mcs.value.get(item, "")

    # General information
    idAddon = xbmcaddon.Addon().getAddonInfo('ID')  # gets name
    icon = xbmcaddon.Addon().getAddonInfo('icon')
    fanart = xbmcaddon.Addon().getAddonInfo('fanart')
    path_folder = xbmcaddon.Addon().getAddonInfo('path')
    name = xbmcaddon.Addon().getAddonInfo('name')  # gets name
    cleanName = re.sub('.COLOR (.*?)]', '', name.replace('[/COLOR]', ''))
    value = {}  # it contains all the settings from xml file
    fileName = path.join(path_folder, "resources", "settings.xml")
    if path.isfile(fileName):
        with open(fileName, 'r') as fp:
            data = fp.read()
        for key in re.findall('id="(\w+)"', data):
            value[key] = get_setting(key)  # reading the values from xbmcaddon.Addon().xml
        if 'url_address' in value and value['url_address'].endswith('/'):
            value['url_address'] = value['url_address'][:-1]


class Settings(object):
    def __init__(self):
        pass

    __metaclass__ = MetaSettings
    pass


# filtering
class Filtering:
    def __init__(self):
        pass

    id_addon = xbmcaddon.Addon().getAddonInfo('id')  # gets name
    time_noti = xbmcaddon.Addon().getSetting('time_noti')
    time_noti = int(time_noti) if time_noti is not '' else 1500  # time notification
    icon = xbmcaddon.Addon().getAddonInfo('icon')
    name_provider = re.sub('.COLOR (.*?)]', '', xbmcaddon.Addon().getAddonInfo('name').replace('[/COLOR]', ''))
    reason = ''
    title = ''
    items = []
    results = []
    type = "general"
    quality_allow = ['*']
    quality_deny = []
    max_size = 10.00  # 10 it is not limit
    min_size = 0.00
    # size
    if xbmcaddon.Addon().getSetting('movie_min_size') == '':
        movie_min_size = 0.0
    else:
        movie_min_size = float(xbmcaddon.Addon().getSetting('movie_min_size'))
    if xbmcaddon.Addon().getSetting('movie_max_size') == '':
        movie_max_size = 10.0
    else:
        movie_max_size = float(xbmcaddon.Addon().getSetting('movie_max_size'))
    if xbmcaddon.Addon().getSetting('TV_min_size') == '':
        TV_min_size = 0.0
    else:
        TV_min_size = float(xbmcaddon.Addon().getSetting('TV_min_size'))
    if xbmcaddon.Addon().getSetting('TV_max_size') == '':
        TV_max_size = 10.0
    else:
        TV_max_size = float(xbmcaddon.Addon().getSetting('TV_max_size'))

    # movie
    movie_qua1 = xbmcaddon.Addon().getSetting('movie_qua1')  # 480p
    movie_qua2 = xbmcaddon.Addon().getSetting('movie_qua2')  # HDTV
    movie_qua3 = xbmcaddon.Addon().getSetting('movie_qua3')  # 720p
    movie_qua4 = xbmcaddon.Addon().getSetting('movie_qua4')  # 1080p
    movie_qua5 = xbmcaddon.Addon().getSetting('movie_qua5')  # 3D
    movie_qua6 = xbmcaddon.Addon().getSetting('movie_qua6')  # CAM
    movie_qua7 = xbmcaddon.Addon().getSetting('movie_qua7')  # TeleSync
    movie_qua8 = xbmcaddon.Addon().getSetting('movie_qua8')  # Trailer
    # Accept File
    movie_key_allowed = xbmcaddon.Addon().getSetting('movie_key_allowed').replace(', ', ',').replace(' ,', ',')
    movie_allow = re.split(',', movie_key_allowed)
    if movie_qua1 == 'Accept File':
        movie_allow.append('480p')
    if movie_qua2 == 'Accept File':
        movie_allow.append('HDTV')
    if movie_qua3 == 'Accept File':
        movie_allow.append('720p')
    if movie_qua4 == 'Accept File':
        movie_allow.append('1080p')
    if movie_qua5 == 'Accept File':
        movie_allow.append('3D')
    if movie_qua6 == 'Accept File':
        movie_allow.append('CAM')
    if movie_qua7 == 'Accept File':
        movie_allow.extend(['TeleSync', ' TS '])
    if movie_qua8 == 'Accept File':
        movie_allow.append('Trailer')
    # Block File
    movie_key_denied = xbmcaddon.Addon().getSetting('movie_key_denied').replace(', ', ',').replace(' ,', ',')
    movie_deny = re.split(',', movie_key_denied)
    if movie_qua1 == 'Block File':
        movie_deny.append('480p')
    if movie_qua2 == 'Block File':
        movie_deny.append('HDTV')
    if movie_qua3 == 'Block File':
        movie_deny.append('720p')
    if movie_qua4 == 'Block File':
        movie_deny.append('1080p')
    if movie_qua5 == 'Block File':
        movie_deny.append('3D')
    if movie_qua6 == 'Block File':
        movie_deny.append('CAM')
    if movie_qua7 == 'Block File':
        movie_deny.extend(['TeleSync', '?TS?'])
    if movie_qua8 == 'Block File':
        movie_deny.append('Trailer')
    if '' in movie_allow:
        movie_allow.remove('')
    if '' in movie_deny:
        movie_deny.remove('')
    if len(movie_allow) == 0:
        movie_allow = ['*']

    # TV
    TV_qua1 = xbmcaddon.Addon().getSetting('TV_qua1')  # 480p
    TV_qua2 = xbmcaddon.Addon().getSetting('TV_qua2')  # HDTV
    TV_qua3 = xbmcaddon.Addon().getSetting('TV_qua3')  # 720p
    TV_qua4 = xbmcaddon.Addon().getSetting('TV_qua4')  # 1080p
    # Accept File
    TV_key_allowed = xbmcaddon.Addon().getSetting('TV_key_allowed').replace(', ', ',').replace(' ,', ',')
    TV_allow = re.split(',', TV_key_allowed)
    if TV_qua1 == 'Accept File':
        TV_allow.append('480p')
    if TV_qua2 == 'Accept File':
        TV_allow.append('HDTV')
    if TV_qua3 == 'Accept File':
        TV_allow.append('720p')
    if TV_qua4 == 'Accept File':
        TV_allow.append('1080p')
    # Block File
    TV_key_denied = xbmcaddon.Addon().getSetting('TV_key_denied').replace(', ', ',').replace(' ,', ',')
    TV_deny = re.split(',', TV_key_denied)
    if TV_qua1 == 'Block File':
        TV_deny.append('480p')
    if TV_qua2 == 'Block File':
        TV_deny.append('HDTV')
    if TV_qua3 == 'Block File':
        TV_deny.append('720p')
    if TV_qua4 == 'Block File':
        TV_deny.append('1080p')
    if '' in TV_allow:
        TV_allow.remove('')
    if '' in TV_deny:
        TV_deny.remove('')
    if len(TV_allow) == 0:
        TV_allow = ['*']

    @classmethod
    def add(cls, title="", url=""):
        if title is not "" and url is not "":
            cls.items.append((title, url))

    @classmethod
    def use_movie(cls):
        cls.quality_allow = cls.movie_allow
        cls.quality_deny = cls.movie_deny
        cls.min_size = cls.movie_min_size
        cls.max_size = cls.movie_max_size

    @classmethod
    def use_tv(cls):
        cls.quality_allow = cls.TV_allow
        cls.quality_deny = cls.TV_deny
        cls.min_size = cls.TV_min_size
        cls.max_size = cls.TV_max_size

    @classmethod
    def information(cls):
        log.info('[%s] Accepted Keywords: %s' % (cls.id_addon, str(cls.quality_allow)))
        log.info('[%s] Blocked Keywords: %s' % (cls.id_addon, str(cls.quality_deny)))
        log.info('[%s] min Size: %s' % (cls.id_addon, str(cls.min_size) + ' GB'))
        log.info(
            '[%s] max Size: %s' % (cls.id_addon, (str(cls.max_size) + ' GB') if cls.max_size != 10 else 'MAX'))

    # validate keywords
    @staticmethod
    def included(value, keys, strict=False):
        value = ' ' + value + ' '
        if '*' in keys:
            res = True
        else:
            res1 = []
            for key in keys:
                res2 = []
                for item in re.split('\s', key):
                    item = item.replace('?', ' ').replace('_', '')
                    if strict:
                        item = ' ' + item + ' '  # it makes that strict the comparation
                    if item.upper() in value.upper():
                        res2.append(True)
                    else:
                        res2.append(False)
                res1.append(all(res2))
            res = any(res1)
        return res

    # validate size
    @classmethod
    def size_clearance(cls, size):
        max_size1 = 100 if cls.max_size == 10 else cls.max_size
        res = False
        value = get_float(size)
        value *= 0.001 if 'M' in size else 1
        if cls.min_size <= value <= max_size1:
            res = True
        return res

    @staticmethod
    def normalize(name):
        from unicodedata import normalize
        import types

        if types.StringType == type(name):
            unicode_name = unicode(name, 'utf-8', 'ignore')
        else:
            unicode_name = name
        normalize_name = normalize('NFKD', unicode_name)
        return normalize_name.encode('ascii', 'ignore')

    @staticmethod
    def un_code_name(name):  # convert all the &# codes to char, remove extra-space and normalize
        from HTMLParser import HTMLParser

        name = name.replace('<![CDATA[', '').replace(']]', '')
        name = HTMLParser().unescape(name.lower())
        return name

    @staticmethod
    def unquote_name(name):  # convert all %symbols to char
        from urllib import unquote

        return unquote(name).decode("utf-8")

    @classmethod
    def safe_name(cls, value):  # make the name directory and filename safe
        value = cls.normalize(value)  # First normalization
        value = cls.unquote_name(value)
        value = cls.un_code_name(value)
        value = cls.normalize(
            value)  # Last normalization, because some unicode char could appear from the previous steps
        value = value.lower().title()
        keys = {'"': ' ', '*': ' ', '/': ' ', ':': ' ', '<': ' ', '>': ' ', '?': ' ', '|': ' ',
                "'": '', 'Of': 'of', 'De': 'de', '.': ' ', ')': ' ', '(': ' ', '[': ' ', ']': ' ', '-': ' '}
        for key in keys.keys():
            value = value.replace(key, keys[key])
        value = ' '.join(value.split())
        return value.replace('S H I E L D', 'SHIELD')

    # verify
    @classmethod
    def verify(cls, name, size):
        if name is None or name is '':
            cls.reason = name.replace(' - ' + cls.name_provider, '') + ' ***Empty Name***'
            return False
        name = cls.safe_name(name)
        cls.title = cls.safe_name(cls.title)
        cls.reason = name.replace(' - ' + cls.name_provider, '') + ' ***Blocked File by'
        if cls.included(name, [cls.title], True):
            result = True
            if name is not None:
                if not cls.included(name, cls.quality_allow) or cls.included(name, cls.quality_deny):
                    cls.reason += ", Keyword"
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


class Magnet:
    def __init__(self, magnet):
        self.magnet = magnet + '&'
        # hash
        info_hash = re.search('urn:btih:(.*?)&', self.magnet)
        result = ''
        if info_hash is not None:
            result = info_hash.group(1)
        self.hash = result
        # name
        name = re.search('dn=(.*?)&', self.magnet)
        result = ''
        if name is not None:
            result = name.group(1).replace('+', ' ')
        self.name = result.title()
        # trackers
        self.trackers = re.findall('tr=(.*?)&', self.magnet)


def generate_payload(generator=None, read_magnet_link=False):
    Filtering.information()  # print filters xbmcaddon.Addon()
    results = []
    cont = 0
    for name, magnet, size, seeds, peers in generator:
        # info_magnet = common.Magnet(magnet)
        if Filtering.verify(name, size):
            cont += 1
            if read_magnet_link:
                magnet = get_links(magnet)  # magnet
            results.append({"name": name,
                            "uri": magnet,
                            # "info_hash": info_magnet.hash,
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
            log.warning(Filtering.reason)
    log.info('>>>>>>' + str(cont) + ' torrents sent to Quasar<<<<<<<')
    return results


def process(separator="%20", generator=None, read_magnet_link=False):
    from threading import Thread
    threads = []

    t = Thread(target=execute_process, args=(separator, generator, read_magnet_link))
    threads.append(t)

    # Start all threads
    for x in threads:
        x.start()

    # Wait for all of them to finish
    for x in threads:
        x.join()

    return Filtering.results


def execute_process(separator="%20", generator=None, read_magnet_link=False):
    for query, url in Filtering.items:
        if 'movie' == Filtering.type:
            Filtering.use_movie()
        elif 'show' == Filtering.type:
            Filtering.use_tv()
            query = exception(query)  # CSI series problem
        elif 'anime' == Filtering.type:
            Filtering.use_tv()
        Filtering.title = query + ' ' + Settings["extra"]  # to do filtering by name
        if Filtering.time_noti > 0:
            from xbmcgui import Dialog
            dialog = Dialog()
            dialog.notification(Filtering.name_provider,
                                query.title(),
                                Filtering.icon,
                                Filtering.time_noti)
            del Dialog
        url_search = url.rstrip().replace(' ', separator)
        log.info(url_search)
        Browser.open(url_search)
        Filtering.results.extend(generate_payload(generator(Browser.content), read_magnet_link))
