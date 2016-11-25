# -*- coding: utf-8 -*-

import re
import urllib2
from cookielib import LWPCookieJar
from time import sleep
from urllib import urlencode, quote

import logger

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36" \
             " (KHTML, like Gecko) Chrome/30.0.1599.66 Safari/537.36"


# provider web browser with cookies management
class Browser:
    def __init__(self):
        pass

    _cookies = None
    cookies = LWPCookieJar()
    content = None
    status = None
    headers = dict()

    @classmethod
    def create_cookies(cls, payload):

        cls._cookies = urlencode(payload)

    # to open any web page
    @classmethod
    def open(cls, url='', language='en', post_data=None, get_data=None):
        if post_data is None:
            post_data = {}
        if get_data is not None:
            url += '?' + urlencode(get_data)
        logger.log.debug(url)
        result = True
        if len(post_data) > 0:
            cls.create_cookies(post_data)
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
            sleep(0.5)  # good spider
            response = opener.open(req)  # send cookies and open url
            cls.headers = response.headers
            # borrow from provider.py Steeve
            if response.headers.get("Content-Encoding", "") == "gzip":
                import zlib
                cls.content = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(response.read())
            else:
                cls.content = response.read()
            response.close()
            cls.status = 200
            logger.log.debug("Status: " + str(cls.status))
            # logger.log.debug(str(cls.content))
        except urllib2.HTTPError as e:
            cls.status = e.code
            logger.log.warning("Status: " + str(cls.status))
            result = False
            if e.code == 503:
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
            logger.log.warning("Status: " + str(cls.status))
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


# open torrent and return the information
def read_torrent(page=''):
    result = ''
    link = get_links(page)
    if Browser.open(link):
        result = Browser.content
    return result


# get the first magnet or torrent from one webpage
def get_links(page=None):
    result = ''
    if page is not None:
        if Browser.open(quote(page).replace("%3A", ":")):
            content = re.findall('http(.*?).torrent["\']', Browser.content)
            if content is not None and len(content) > 0:
                result = 'http' + content[0] + '.torrent'
            else:
                content = re.findall('magnet:\?[^\'"\s<>\[\]]+', Browser.content)
                if content is not None and len(content) > 0:
                    result = 'http://itorrents.org/torrent/%s.torrent ' % Magnet(content[0]).info_hash
    return result


class Magnet:
    def __init__(self, magnet):
        self.magnet = magnet + '&'
        # hash
        info_hash = re.search('urn:btih:(.*?)&', self.magnet)
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
