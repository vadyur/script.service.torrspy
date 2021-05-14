# -*- coding: utf-8 -*-

import sys
#from vdlib.scrappers.movieapi import imdb_cast
from sys import version_info

from vdlib.util import filesystem
from .torrspy.info import addon_title, make_path_to_base_relative, load_video_info, save_video_info, save_art, addon_base_path
from .torrspy.player_video_info import PlayerVideoInfo

if version_info >= (3, 0):
    from urllib.parse import urlparse, parse_qs
else:
    from urlparse import urlparse, parse_qs    # type: ignore

from torrserve_stream import Settings
ts_settings = Settings()

def log(s):
    from .torrspy.info import addon_id
    message = '[{}: script.py]: {}'.format(addon_id, s)
    import xbmc
    xbmc.log(message)

def playing_torrserver_source():
    import xbmc
    player = xbmc.Player()

    if player.isPlayingVideo():
        name = player.getPlayingFile()
        if name:
            if ':{}/'.format(ts_settings.port) in name:
                return True
    return False

def alert(s):
    import xbmcgui
    xbmcgui.Dialog().ok('TorrSpy', s)

def get_params(url):
    res = urlparse(url)
    return parse_qs(res.query)

def update_library(path=None, on_update=None):
    import xbmc

    class MyMonitor(xbmc.Monitor):
        def onScanFinished(self, library):
            if on_update():
                self.done = True
    monitor = MyMonitor()
    monitor.done = False

    #if path:
    #    xbmc.executebuiltin('UpdateLibrary("video","{}")'.format(path), wait=True)
    #else:
    xbmc.executebuiltin('UpdateLibrary("video")')

    while not monitor.abortRequested():
        if monitor.done or monitor.waitForAbort(2):
            break


def save_strm(file_path, play_url, sort_index):
    # action="play_now", magnet=magneturi, selFile=0
    from vdlib.util import urlencode
    from vdlib.kodi.compat import makeLegalFilename

    file_path = makeLegalFilename(file_path)

    log('def save_strm(file_path, play_url)')
    log('file_path is "{}"'.format(file_path))

    base_path = addon_base_path()
    strm_path = filesystem.relpath(file_path, base_path)

    params = {
            'action' : 'play_strm',
            'play_url': play_url,
            'sort_index': sort_index,
            'strm_path': strm_path
        }
    queryString = urlencode(params, encoding='utf-8')

    link = 'plugin://{}/?{}'.format(
        'plugin.video.torrserve-next',
        queryString
    )

    log('link is {}'.format(link))

    with filesystem.fopen(file_path, 'w') as out:
        out.write(link)

def save_movie(player_video_info):
    video_info = player_video_info.video_info
    play_url = player_video_info.play_url
    sort_index = player_video_info.sort_index

    original_title = video_info.get('originaltitle')
    year = video_info.get('year')
    if original_title and year:
        import xbmcgui
        save_to_lib = xbmcgui.Dialog().yesno(addon_title(), 
                u'Кино не досмотрено. Сохранить его в медиатеку для последующего просмотра?')
        if not save_to_lib:
            return

        name = u'{} ({})'.format(original_title, year)
        log('name is {}'.format(name))
        playing_strm = make_path_to_base_relative('Movies/' + name + '.strm')
        save_strm(playing_strm, play_url, sort_index)
        #    nfo = name + '.nfo'

        def on_update_library():
            result = get_movies_by('Movies', name + '.strm')
            movies = result.get('movies')
            if movies:
                movie = movies[0]
                set_movie_resume_playcount(movie['movieid'], player_video_info)

            return True

        update_library(make_path_to_base_relative('Movies'), on_update_library)

def get_movies_by(dirname, filename, fields=["file"]):
    filter = find_file_filter(dirname, filename)

    from vdlib.kodi.jsonrpc_requests import VideoLibrary
    result = VideoLibrary.GetMovies(filter=filter, properties=fields)    
    return result

def get_episodes_by(dirname, filename, fields=["file"]):
    filter = find_file_filter(dirname, filename)

    from vdlib.kodi.jsonrpc_requests import VideoLibrary
    result = VideoLibrary.GetEpisodes(filter=filter, properties=fields)    
    return result

def find_file_filter(dirname, filename):
    filter = {'and': [{
                    "operator": "contains",
                    "field": "path",
                    "value": dirname
                },
                {
                    "operator": "is",
                    "field": "filename",
                    "value": filename
                }                
            ]}
    return filter

def get_recent_episodes(fields):
    import datetime
    today = datetime.date.today()
    today.strftime('%Y-%m-%d')

    from vdlib.kodi.jsonrpc_requests import VideoLibrary

    filter = {
        "operator": "startswith",
        "field": "dateadded",
        "value": today.strftime('%Y-%m-%d')
    }
    limits = {
        "start": 0,
        "end": 100
    }
    sort = {
        "method": "dateadded",
        "order": "descending"
    }
    properties = [
        "title",
        "thumbnail",
        "playcount",
        "lastplayed",
        "dateadded",
        "episode",
        "season",
        "rating",
        "file",
        "cast",
        "showtitle",
        "tvshowid",
        "uniqueid",
        "resume",
        "firstaired",
        "fanart"
    ]
    result = VideoLibrary.GetEpisodes(filter=filter, limits=limits, sort=sort, properties=fields)

def set_movie_resume_playcount(movieid, player_video_info):
    from vdlib.kodi.jsonrpc_requests import VideoLibrary
    player_video_info = player_video_info  # type: PlayerVideoInfo
    percent = player_video_info.time / player_video_info.total_time * 100
    if player_video_info.time > 180:
        if percent < 90:
            resume = {'position': player_video_info.time,
                         'total': player_video_info.total_time}
            result = VideoLibrary.SetMovieDetails(movieid=movieid,resume=resume)
        else:
            result = VideoLibrary.SetMovieDetails(movieid=movieid,playcount=1)
    pass

def set_episode_resume_playcount(episodeid, player_video_info):
    from vdlib.kodi.jsonrpc_requests import VideoLibrary

    player_video_info = player_video_info  # type: PlayerVideoInfo
    percent = player_video_info.time / player_video_info.total_time * 100
    if player_video_info.time > 180:
        if percent < 90:
            resume = {'position': player_video_info.time,
                         'total': player_video_info.total_time}
            result = VideoLibrary.SetEpisodeDetails(episodeid=episodeid,resume=resume)
        else:
            result = VideoLibrary.SetEpisodeDetails(episodeid=episodeid,playcount=1)
    pass

def save_tvshow(player_video_info):
    player_video_info = player_video_info  # type: PlayerVideoInfo
    video_info = player_video_info.video_info
    original_title = video_info.get('originaltitle')
    year = video_info.get('year')
    imdb = video_info.get('imdbnumber')
    if original_title and year:
        import xbmcgui
        save_to_lib = xbmcgui.Dialog().yesno(addon_title(), 
                u'Вы смотрели эпизод сериала. Сохранить сериал в медиатеку для последующего просмотра?')

        if not save_to_lib:
            return

        from vdlib.util import filesystem
        tvshow_dirname = u'{} ({})'.format(original_title, year)
        log(tvshow_dirname)

        part_dirname = filesystem.join('TVShows', tvshow_dirname)
        tvshow_path = make_path_to_base_relative(part_dirname)
        if not filesystem.exists(tvshow_path):
            filesystem.makedirs(tvshow_path)

        from vdlib.scrappers.tvshowapi import TVShowAPI, parse_torrent
        api = TVShowAPI(original_title, video_info.get('title'), imdb)

        from torrserve_stream import Engine

        hash = Engine.extract_hash_from_play_url(player_video_info.play_url)
        log(hash)
        ts_engine = Engine(hash=hash, host=ts_settings.host, port=ts_settings.port)

        info = {'name': ts_engine.stat().get('Name'), 
                'files': []}
        ts_engine_files = ts_engine.files()
        for f in ts_engine_files:
            path = f['path'].split('/')
            info['files'].append({'path': path})

        playing_strm = None
        files = parse_torrent(info)
        for item in files:
            if not api.Episode(item['season'], item['episode']):
                continue

            season_path = filesystem.join(tvshow_path, 'Season {}'.format(item['season']))
            if not filesystem.exists(season_path):
                filesystem.makedirs(season_path)
            filename = '{} ({}) S{:02d}E{:02d}.strm'.format(original_title, year, item['season'], item['episode'])
            sort_index = item['index']
            play_url = ts_engine.play_url(sort_index)
            strm_path = filesystem.join(season_path, filename)
            save_strm(strm_path, play_url, sort_index)

            if play_url == player_video_info.play_url:
                playing_strm = filename

        def on_update_library():
            if not playing_strm:
                return True

            result = get_episodes_by(part_dirname, playing_strm)
            episodes = result.get('episodes')
            if episodes:
                episode = episodes[0]
                set_episode_resume_playcount(episode['episodeid'], player_video_info)

            return True

        update_library(tvshow_path, on_update_library)


def get_info():
    log('---TorrSpy: get_info---')
    import xbmc, xbmcgui
    xbmc.sleep(2*1000)
    item = xbmcgui.ListItem()
    url = xbmc.Player().getPlayingFile()
    item.setPath(url)

    from torrserve_stream import Engine

    hash = Engine.extract_hash_from_play_url(url)
    engine = Engine(hash=hash, host=ts_settings.host, port=ts_settings.port)

    video_info = engine.get_video_info()
    if video_info:
        log('Get info from TorrServer')

    art = engine.get_art()

    if not video_info:
        video_info = load_video_info(hash)

    if not video_info:
        log('Extract info')
        from .detect import extract_title_date, extract_filename     # type: ignore
        filename = extract_filename(url)
        title, year = extract_title_date(filename)
        video_info = {'title': title, 'year': year}

    def update_listitem(video_info, art):
        if video_info: item.setInfo('video', video_info)
        if art: item.setArt(art)

        xbmc.Player().updateInfoTag(item)

    log('---TorrSpy---')
    log(xbmc.Player().getPlayingFile())

    update_listitem(video_info, art)

    if 'imdbnumber' not in video_info:
        from .detect import find_tmdb_movie_item
        tmdb_movie_item = find_tmdb_movie_item(video_info)
        imdbnumber = tmdb_movie_item.imdb()
        video_info.update(tmdb_movie_item.get_info())
        if imdbnumber:
            video_info['imdbnumber'] = imdbnumber
        if tmdb_movie_item.type == 'movie':
            video_info['mediatype'] = 'movie'
        elif video_info['mediatype'] == 'tv':
            video_info['mediatype'] = 'tvshow'

        update_listitem(video_info, art)

    save_video_info(hash, video_info)
    save_art(hash, art)

def open_settings():
    import xbmcaddon
    addon = xbmcaddon.Addon()
    addon.openSettings()

def create_playlists():    
    from vdlib.kodi.compat import translatePath
    src_dir = translatePath('special://home/addons/script.service.torrspy/resources/playlists')
    dst_dir = translatePath('special://profile/playlists/video')

    from xbmcvfs import copy, listdir
    from os.path import join
    _, files = listdir(src_dir)
    for file in files:
        copy(join(src_dir, file), join(dst_dir, file))

    from xbmc import executebuiltin
    executebuiltin('ActivateWindow(Videos, {}, return)'.format('special://profile/playlists/video'))

def create_sources():
    from xbmcgui import Dialog
    from xbmcaddon import Addon
    from xbmc import executebuiltin

    base_path = addon_base_path()
    restart_msg = u'Чтобы изменения вступили в силу, нужно перезапустить KODI. Перезапустить?'

    from vdlib.kodi.sources import create_movies_and_tvshows
    if create_movies_and_tvshows(base_path, scrapper='metadata.themoviedb.org', scrapper_tv='metadata.tvshows.themoviedb.org', suffix=' - TorrSpy'):
        if Dialog().yesno(addon_title(), restart_msg):
            executebuiltin('Quit')

def end_playback(player_video_info_str):
    pvi = PlayerVideoInfo(None)
    pvi.loads(player_video_info_str)

    video_info  = pvi.video_info
    play_url    = pvi.play_url
    sort_index  = pvi.sort_index

    if not video_info:
        log('video_info does not exists')
        return

    if pvi.time and pvi.total_time:
        percent = pvi.time / pvi.total_time * 100
        log('percent is {}'.format(percent))
        log('pvi.time is {}'.format(pvi.time))

        if pvi.media_type == 'movie':
            if pvi.time >= 180 and percent < 90: 
                save_movie(pvi)
        elif pvi.media_type == 'tvshow':
            if percent >= 50:
                save_tvshow(pvi)

        log("media_type = '{}'".format(pvi.media_type))

def main():
    #Runner(sys.argv[0])
    log('---TorrSpy---')
    for i in sys.argv:
        log(i)
    log('---TorrSpy---')

    def arg_exists(arg, index):
        try:
            return sys.argv.index(arg) == index
        except ValueError:
            return False

    if arg_exists('get_info', 1):
        get_info()
    elif arg_exists('end_playback', 1):
        end_playback(sys.argv[2])
    elif arg_exists('create_playlists', 1):
        create_playlists()
    elif arg_exists('create_sources', 1):
        create_sources()
    else:
        open_settings()