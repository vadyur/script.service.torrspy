import urllib
import xbmc, xbmcgui, xbmcaddon

from sys import version_info

if version_info >= (3, 0, 0):
    from urllib.parse import quote_plus
else:
    from urllib import quote_plus

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_path = addon.getAddonInfo('path')

def log(s):
    message = '[{}]: {}'.format(addon_id, s)
    xbmc.log(message)

def make_url(action):
    if action:
        params_str = quote_plus(action)
        url = 'plugin://{}/{}'.format(addon_id, params_str)
    else:
        url = 'plugin://{}'.format(addon_id)
    return url

def RunPlugin(action):
    import xbmc
    url = make_url(action)
    xbmc.executebuiltin('RunPlugin("%s")' % url)

def RunScript(*args):
    import xbmc, os

    path = os.path.join(addon_path, 'src', 'script.py')
    args = [ str(i) for i in args ]
    param_str = ', '.join(args)
    xbmc.executebuiltin('RunScript({}, {})'.format(path, param_str))

def Test():
    # testing
    RunPlugin("run")

class MyMonitor(xbmc.Monitor):
    pass

title = 'My cool new title'

class MyPlayer(xbmc.Player):

    title = None
    tagline = '##TorrSpy##'

    def onAVStarted(self):
        log('MyPlayer.onAVStarted')

        #    def onPlayBackStarted(self):
        #        log('MyPlayer.onPlayBackStarted')

        tag = self.getVideoInfoTag()
        file  = self.getPlayingFile()

        log('\tMyPlayer.file = {}'.format(file))
        log('\tMyPlayer.getTitle() = {}'.format(tag.getTitle()))

        from script import playing_torrserver_source

        if tag.getTagLine() != self.tagline:

            if playing_torrserver_source():
                log('reopen stream')

                item = xbmcgui.ListItem()
                item.setPath(file)
                item.setInfo('video', {'tagline' : self.tagline})
                self.play(file, item, False)


if __name__ == '__main__':
    monitor = MyMonitor()
    player = MyPlayer()

    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            break

        if not player.isPlaying():
            continue

        try:
            vit = player.getVideoInfoTag()
        except RuntimeError:
            continue

        if vit.getTagLine() == player.tagline:
            item = xbmcgui.ListItem()
            url = player.getPlayingFile()
            item.setPath(url)
            item.setInfo('video', 
                        {'tagline': '',})
            player.updateInfoTag(item)

            RunScript('get_info')
