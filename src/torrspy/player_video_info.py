# -*- coding: utf-8 -*-

import pickle, base64

def get_sort_index(play_url):
    from torrserve_stream import Engine
    from torrserve_stream import Settings
    ts_settings = Settings()

    hash = Engine.extract_hash_from_play_url(play_url)
    name = Engine.extract_filename_from_play_url(play_url)

    engine = Engine(hash=hash, host=ts_settings.host, port=ts_settings.port, auth=ts_settings.auth)
    return engine.get_ts_index(name)

class PlayerVideoInfo(object):
    def __init__(self, player):
        import xbmc
        self.player = player        # type: xbmc.Player
        self.reset()

    def update(self):
        if self.player.isPlayingVideo():
            try:
                video_info_tag  = self.player.getVideoInfoTag()

                self.time       = self.player.getTime()
                self.total_time = self.player.getTotalTime()

                self.video_info = self.player.getVideoInfo()
                self.media_type = video_info_tag.getMediaType()

                self.play_url   = self.player.getPlayingFile()
                self.sort_index = get_sort_index(self.play_url)
            except BaseException:
                from vdlib.util.log import print_tb
                print_tb()
                self.reset()

    def reset(self):
        self.time       = None
        self.total_time = None
        self.video_info = None
        self.media_type = None
        self.play_url   = None
        self.sort_index = None

    def dumps(self):
        data = self.__dict__.copy()
        data.pop('player')
        s = pickle.dumps(data)
        s = base64.b64encode(s)
        if isinstance(s, str):
            return s
        else:
            return s.decode('ascii')

    def loads(self, s):
        bb = base64.b64decode(s)
        d = pickle.loads(bb)
        self.__dict__.update(d)

def test():
    video_info = {
        'originaltitle': "FBI",
        'title': u"ФБР",
        'year': 2018
    }

    pvi = PlayerVideoInfo(None)
    pvi.video_info = video_info
    pvi.time       = 1234
    pvi.total_time = 2345
    pvi.media_type = 'tvshow'
    pvi.play_url   = 'http://host:8090/dskfhsdk/hdsfkhs'
    pvi.sort_index = 1

    s = pvi.dumps()
    pvi2 = PlayerVideoInfo(None)
    pvi2.loads(s)

    pass


if __name__ == '__main__':
    test()
    