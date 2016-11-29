# -*- coding: utf-8 -*-
# Name:        browser.py
# Author:      Mancuniancol
# Created on:  28.11.2016
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Mini Browser
url = "http://example.com"
if Browser.open(url):
    print Browser.content

Using cloudhole
Using with GET request
url = "http://example.com"
Browser.get_cloudhole_key()
if Browser.open(url):
    print Browser.content

Using with GET request
data = {"value1": "12", "value1": "abc"}
url = "http://example.com"
if Browser.open(url, get_data=data):
    print Browser.content

Using with POST request
data = {"value1": "12", "value1": "abc"}
url = "http://example.com"
if Browser.open(url, post_data=data):
    print Browser.content
"""

import json
import re
import urllib2
from cookielib import Cookie, LWPCookieJar
from os import path
from time import sleep, time
from urllib import urlencode, quote
from urlparse import urlparse

from xbmc import translatePath

import logger

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36" \
             " (KHTML, like Gecko) Chrome/30.0.1599.66 Safari/537.36"
PATH_TEMP = translatePath("special://temp")
CLEARANCE = None


def _log_debug(message=''):
    """
    Call Logger debug
    :param message: message to the log
    :type message: str
    :return:
    """
    logger.log.debug(message)


def _log_warning(message=''):
    """
    Call Logger warning
    :param message: message to the log
    :type message: str
    :return:
    """
    logger.log.warning(message)


class Browser:
    """
    Mini Web Browser with cookies handle
    """
    _counter = 0
    _cookies_filename = ''
    _cookies = LWPCookieJar()
    cloudhole_key = None
    content = None
    status = None
    headers = dict()

    def __init__(self):
        pass

    @classmethod
    def _create_cookies(cls, payload):
        return urlencode(payload)

    @classmethod
    def _read_cookies(cls, url=''):
        cls._cookies_filename = path.join(PATH_TEMP, urlparse(url).netloc + '.jar')
        if path.exists(cls._cookies_filename):
            try:
                cls._cookies.load(cls._cookies_filename)
            except Exception as e:
                _log_debug("Reading cookies error: %s" % repr(e))
                pass

        # Check for cf_clearance cookie provided by scakemyer
        # https://github.com/scakemyer/cloudhole-api
        if not any(cookie.name == 'cf_clearance' for cookie in cls._cookies):
            global USER_AGENT
            global CLEARANCE
            if cls.cloudhole_key and CLEARANCE is None:
                try:
                    r = urllib2.Request("https://cloudhole.herokuapp.com/clearances")
                    r.add_header('Content-type', 'application/json')
                    r.add_header('Authorization', cls.cloudhole_key)
                    res = urllib2.urlopen(r)
                    content = res.read()
                    _log_debug("CloudHole returned: %s" % content)
                    data = json.loads(content)
                    USER_AGENT = data[0]['userAgent']
                    CLEARANCE = data[0]['cookies']
                    _log_debug("New UA and clearance: %s / %s" % (USER_AGENT, CLEARANCE))
                except Exception as e:
                    _log_debug("CloudHole error: %s" % repr(e))
                    pass
            if CLEARANCE:
                t = str(int(time()) + 604800)
                c = Cookie(None, 'cf_clearance', CLEARANCE[13:], None, False,
                           '.{uri.netloc}'.format(uri=urlparse(url)), True, True,
                           '/', True, False, t, False, None, None, None, False)
                cls._cookies.set_cookie(c)

    @classmethod
    def _save_cookies(cls):
        try:
            cls._cookies.save(cls._cookies_filename)
        except Exception as e:
            _log_debug("Saving cookies error: %s" % repr(e))
            pass

    @classmethod
    def _good_spider(cls):
        """
        Delay of 0.5 seconds to to call too many requests per second. Some pages start to block
        """
        cls._counter += 1
        if cls._counter > 1:
            sleep(0.5)  # good spider

    @classmethod
    def cookies(cls):
        """
        Cookies
        :return: LWPCookieJar format.
        """
        return cls._cookies

    @classmethod
    def open(cls, url='', language='en', post_data=None, get_data=None):
        """
        Open a web page and returns its contents
        :param url: url address web page
        :type url: str
        :param language: language encoding web page
        :type language: str
        :param post_data: parameters for POST request
        :type post_data: dict
        :param get_data: parameters for GET request
        :type get_data: dict
        :return: True if the web page was opened successfully. False, otherwise.
        """
        # Creating request
        if post_data is None:
            post_data = {}
        if get_data is not None:
            url += '?' + urlencode(get_data)
        _log_debug(url)

        result = True
        data = urlencode(post_data) if len(post_data) > 0 else None
        req = urllib2.Request(url, data)

        # Cookies and cloudhole info
        cls._read_cookies(url)
        _log_debug("Cookies: %s" % repr(cls._cookies))
        # open cookie jar
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cls._cookies))

        # Headers
        req.add_header('User-Agent', USER_AGENT)
        req.add_header('Content-Language', language)
        req.add_header("Accept-Encoding", "gzip")

        try:
            cls._good_spider()
            # send cookies and open url
            response = opener.open(req)
            cls.headers = response.headers
            cls._save_cookies()

            # borrow from provider.py Steeve
            if response.headers.get("Content-Encoding", "") == "gzip":
                import zlib
                cls.content = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(response.read())
            else:
                cls.content = response.read()
            response.close()
            cls.status = 200
            _log_debug("Status: " + str(cls.status))

        except urllib2.HTTPError as e:
            cls.status = e.code
            _log_warning("Status: " + str(cls.status))
            result = False
            if e.code == 403:
                _log_warning("CloudFlared at %s" % url)
            elif e.code == 503:
                # trying to open with antibots tool
                sleep(0.5)  # good spider
                import cfscrape
                scraper = cfscrape.create_scraper()  # returns a CloudflareScraper instance
                cls.content = scraper.get(url).content
                cls.status = 200
                logger.log.warning("Trying antibot's measure")
                result = True

        except urllib2.URLError as e:
            cls.status = e.reason
            _log_warning("Status: " + str(cls.status))
            result = False
        return result

    @classmethod
    def login(cls, url='', payload=None, word=''):
        """
        Login to web site
        :param url:  url address from web site
        :type url: str
        :param payload: parameters for the login request
        :type payload: dict
        :param word:  message from the web site when the login fails
        :type word: str
        :return: True if the login was successful. False, otherwise.
        """
        result = False
        if cls.open(url, post_data=payload):
            result = True
            data = cls.content
            if word in data:
                cls.status = 'Wrong Username or Password'
                result = False
        return result


def read_torrent(uri=''):
    """
    Copy a torrent file locally and returns its content
    :param uri:  Uniform Resource Identifier for the torrent
    :type uri: str
    :return: Torrent file contents.
    """
    result = ''
    link = get_links(uri)
    if len(link) > 0 and Browser.open(link):
        result = Browser.content
    return result


def get_links(uri=''):
    """
    Find the magnet information or torrent from web page
    :param uri:  Uniform Resource Identifier for the web page
    :type uri: str
    :return: the torrent file URI.
    """
    result = uri
    if uri is not '' and not uri.endswith('.torrent'):
        if Browser.open(quote(uri).replace("%3A", ":")):
            content = re.findall('magnet:\?[^\'"\s<>\[\]]+', Browser.content)
            if content is not None and len(content) > 0:
                result = 'http://itorrents.org/torrent/%s.torrent' % Magnet(content[0]).info_hash
            else:
                content = re.findall('http(.*?).torrent["\']', Browser.content)
                if content is not None and len(content) > 0:
                    result = 'http' + content[0] + '.torrent'
                    result = result.replace('torcache.net', 'itorrents.org')
    return result


def get_cloudhole_key():
    """
    Get the Cloudhole Key
    """
    cloudhole_key = None
    try:
        r = urllib2.Request("https://cloudhole.herokuapp.com/key")
        r.add_header('Content-type', 'application/json')
        res = urllib2.urlopen(r)
        content = res.read()
        _log_debug("CloudHole returned: %s" % content)
        data = json.loads(content)
        cloudhole_key = data['key']

    except Exception as e:
        _log_debug("Getting CloudHole Key error: %s" % repr(e))
        pass
    return cloudhole_key


class Magnet:
    """
    Create Magnet object with its properties
    """

    def __init__(self, magnet):
        self.magnet = magnet + '&'
        # hash
        info_hash = re.search('urn:btih:(\w+)&', self.magnet, re.IGNORECASE)
        result = ''
        if info_hash is not None:
            result = info_hash.group(1)
        self.info_hash = result
        # name
        name = re.search('dn=(.*?)&', self.magnet)
        result = ''
        if name is not None:
            result = name.group(1).replace('+', ' ')
        self.name = result.title()
        # trackers
        self.trackers = re.findall('tr=(.*?)&', self.magnet)
