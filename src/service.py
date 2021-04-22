import xbmc, xbmcgui, xbmcaddon

from sys import version_info

if version_info >= (3, 0, 0):
    from urllib.parse import quote_plus
else:
    from urllib import quote_plus

from .script import alert, playing_torrserver_source

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_path = addon.getAddonInfo('path')

def log(s):
    message = '[{}: service.py]: {}'.format(addon_id, s)
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

    path = os.path.join(addon_path, 'script.py')
    args = [ str(i) for i in args ]
    param_str = ', '.join(args)
    xbmc.executebuiltin('RunScript({}, {})'.format(path, param_str))

def Test():
    # testing
    RunPlugin("run")

class MyMonitor(xbmc.Monitor):

    def onSettingsChanged(self):
        pass

class MyPlayer(xbmc.Player):

    tagline = '##TorrSpy##'

    def getVideoInfo(self):
        tag = self.getVideoInfoTag()

        result = {}

        if tag.getMediaType() != 'video':
            return result

        def _is_string_type(s):
            if isinstance(s, str):
                return True
            elif version_info < (3, 0) and isinstance(s, unicode):  # type: ignore
                return True
            return False

        def _integer(i):
            return int(i)

        def _string_or_list_of_strings(s):
            if _is_string_type(s) and ',' in s:
                return s.split(',')
            return s

        def _string(s):
            return s

        def _list(l):
            if _is_string_type(l):
                return l.split(',')
            return l

        def _float(f):
            return f

        fields = [
            ('dbid',        tag.getDbId,            _integer),
            ('director',    tag.getDirector,        _string_or_list_of_strings),
            ('credits',     tag.getWritingCredits,  _string_or_list_of_strings),
            ('genre',       tag.getGenre,           _string_or_list_of_strings),
            ('tagline',     tag.getTagLine,         _string),
            ('plotoutline', tag.getPlotOutline,     _string),
            ('plot',        tag.getPlot,            _string),
            ('title',       tag.getTitle,           _string),
            ('originaltitle',tag.getOriginalTitle,  _string),
            ('tvshowtitle', tag.getTVShowTitle,     _string),
            ('votes',       tag.getVotes,           _string),
            ('cast',        tag.getCast,            _list),
            # ('', tag.getFile),
            # ('', tag.getPath),
            # ('', tag.getFilenameAndPath),
            ('imdbnumber',  tag.getIMDBNumber,      _string),
            ('season',      tag.getSeason,          _integer),
            ('episode',     tag.getEpisode,         _integer),
            ('year',        tag.getYear,            _integer),
            ('rating',      tag.getRating,          _float),
            ('userrating',  tag.getUserRating,      _integer),
            ('playcount',   tag.getPlayCount,       _integer),
            ('lastplayed',  tag.getLastPlayed,      _string),
            ('premiered',   tag.getPremiered,       _string),
            # ('', tag.getFirstAired),
            ('trailer',     tag.getTrailer,         _string),
        ]

        for field, func, data_type in fields:
            res = func()
            if res:
                result[field] = data_type(res)

        return result

    def onAVStarted(self):
        log('MyPlayer.onAVStarted')

        #    def onPlayBackStarted(self):
        #        log('MyPlayer.onPlayBackStarted')

        tag = self.getVideoInfoTag()
        file  = self.getPlayingFile()

        log('\tMyPlayer.file = {}'.format(file))
        log('\tMyPlayer.getTitle() = {}'.format(tag.getTitle()))

        if tag.getTitle():
            log('Keep current info')
            return

        if tag.getTagLine() != self.tagline:

            if playing_torrserver_source():

                item = xbmcgui.ListItem()
                item.setPath(file)

                video_info = {'tagline' : self.tagline}
                item.setInfo('video', video_info)

                self.updateInfoTag(item)                
                tag = self.getVideoInfoTag()

                if tag.getTagLine() != self.tagline:
                    log('reopen stream')
                    video_info.update(self.getVideoInfo())
                    item.setInfo('video', video_info)
                    self.play(file, item, False)
                else:
                    log('Keep stream opened')

    def onPlayBackStopped(self):
        log('onPlayBackStopped')
        self.end_playback()

    def onPlayBackEnded(self):
        log('onPlayBackEnded')
        self.end_playback()

    def end_playback(self):
        import vsdbg
        vsdbg.breakpoint()

        if self.video_info.time < self.video_info.total_time:
            message = u'Info:\n\t{}\n\t{}\n\t{}'.format(
                self.video_info.original_title, 
                self.video_info.year, 
                self.video_info.media_type)
            alert(message)
            if self.video_info.media_type == 'movie':
                if self.video_info.original_title and self.video_info.year:
                    name = u'{}({})'.format(self.video_info.original_title, self.video_info.year)
                    strm = name + '.strm'
                    nfo = name + '.nfo'

class VideoInfo(object):
    def __init__(self, player):
        self.player = player

    def update(self):
        if self.player.isPlayingVideo():
            video_info_tag = self.getVideoInfoTag()

            self.time = self.getTime()
            self.total_time = self.getTotalTime()
            self.original_title = video_info_tag.getOriginalTitle()
            self.year = video_info_tag.getYear()
            self.imdbnumber = video_info_tag.getIMDBNumber()
            self.play_count = video_info_tag.getPlayCount()
            self.media_type = video_info_tag.getMediaType()

def main():
    monitor = MyMonitor()
    player = MyPlayer()
    video_info = VideoInfo(player)
    player.video_info = video_info

    while not monitor.abortRequested():
        if monitor.waitForAbort(2):
            break

        if not player.isPlaying():
            continue

        try:
            vit = player.getVideoInfoTag()
        except RuntimeError:
            continue

        video_info.update()

        if vit.getTagLine() == player.tagline:
            log('reset tagline')

            item = xbmcgui.ListItem()
            url = player.getPlayingFile()
            item.setPath(url)
            item.setInfo('video', 
                        {'tagline': '',})
            player.updateInfoTag(item)

            log('RunScript get_info')
            RunScript('get_info')
