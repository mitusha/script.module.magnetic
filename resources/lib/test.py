# import browser
#
# link = 'http://itorrents.org/torrent/C10937099FFFB9BEA1057F71F479298B231189E7.torrent'
#
# browser.Browser.open(link)
#
# print browser.Browser.content
import re
class Magnet:
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

uri = "magnet:?xt=urn:btih:MAGNET:?XT=URN:BTIH:9F17C600156B5FC0D729&dn=%5Bmonova.org%5D+Suicide+Squad+2016+720p+BrRip+x264+-+DIAMOND&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969&tr=udp%3A%2F%2Fexodus.desync.com%3A6969"

print Magnet(uri).info_hash