import sys

from sys import version_info

if version_info >= (3, 0, 0):
    from urllib.parse import urlparse, parse_qs
else:
    from urlparse import urlparse, parse_qs    # type: ignore

from torrserve_stream import Settings

settings = Settings()

def playing_torrserver_source():
    import xbmc
    player = xbmc.Player()

    if player.isPlayingVideo():
        name = player.getPlayingFile()
        if name:
            if ':{}/'.format(settings.port) in name:
                return True
    return False

def alert(s):
    import xbmcgui
    xbmcgui.Dialog().ok('TorrSpy', s)

def get_params(url):
    res = urlparse(url)
    return parse_qs(res.query)

class Runner(object):
    prefix = 'plugin://script.module.torrspy/'
    tag = '##TorrSpy##'

    def __init__(self, url):
        alert(url)

        command = url.replace(Runner.prefix, '')
        self.__getattribute__(command)()
        
    def run(self):
        if playing_torrserver_source():
            import xbmc, xbmcgui, xbmcplugin

            title = 'My cool new title'
            xbmc_player = xbmc.Player()

            vidIT = xbmc_player.getVideoInfoTag()

            if vidIT.getTagLine() == self.tag:
                return

            item = xbmcgui.ListItem()
            url = xbmc_player.getPlayingFile()
            item.setPath(url)
            item.setInfo('video', {'tagline' : self.tag})
            xbmc_player.updateInfoTag(item)


def Test():
    Runner('plugin://script.module.torrspy/run')
    pass

def get_info():
    print('---TorrSpy: get_info---')
    import xbmc, xbmcgui
    xbmc.sleep(10*1000)
    item = xbmcgui.ListItem()
    url = xbmc.Player().getPlayingFile()
    item.setPath(url)

    from torrserve_stream import Engine

    hash = Engine.extract_hash_from_play_url(url)
    engine = Engine(hash=hash, host=settings.host, port=settings.port)

    vi = engine.get_video_info()
    if vi:
        item.setInfo('video', vi)
    else:
        from detect import extract_title_date, extract_filename
        filename = extract_filename(url)
        title, year = extract_title_date(filename)
        item.setInfo('video', 
                        {'title': title,
                        'year': year, 
                        'rating': 7.6,
                        'plot': 'Cool cool cool'})

    art = engine.get_art()
    if art:
        item.setArt(art)

    xbmc.Player().updateInfoTag(item)
    print('---TorrSpy---')
    print(xbmc.Player().getPlayingFile())

def open_settings():
    import xbmcaddon
    addon = xbmcaddon.Addon()
    addon.openSettings()


if __name__ == '__main__':
    #Runner(sys.argv[0])
    print('---TorrSpy---')
    for i in sys.argv:
        print(i)
    print('---TorrSpy---')

    def arg_exists(arg, index):
        try:
            return sys.argv.index(arg) == index
        except ValueError:
            return False

    if arg_exists('get_info', 1):
        get_info()
    else:
        open_settings()