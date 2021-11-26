from torrserve_stream.engine import Engine
from torrserve_stream.settings import Settings

from vdlib.util import filesystem

from .player_video_info import PlayerVideoInfo
from .info import make_path_to_base_relative, addon_base_path

ts_settings = Settings()

def log(s):
    from . import _unit_log
    _unit_log('strm_utils.py', s)

def save_movie(player_video_info):
    # type: (PlayerVideoInfo) -> None

    video_info = player_video_info.video_info
    play_url = player_video_info.play_url
    sort_index = player_video_info.sort_index

    original_title = video_info.get('originaltitle')
    year = video_info.get('year')
    if original_title and year:
        from .info import add_movies_to_lib
        if add_movies_to_lib():
            name = save_movie_strm(play_url, sort_index, original_title, year)

            def on_update_library():
                result = get_movies_by(u'Movies', name + '.strm')
                movies = result.get('movies')
                if movies:
                    movie = movies[0]
                    set_movie_resume_playcount(movie['movieid'], player_video_info)

                return True

            update_library(make_path_to_base_relative('Movies'), on_update_library)

def save_movie_strm(play_url, sort_index, original_title, year):
    from vdlib.util.string import decode_string
    name = u'{} ({})'.format(
                decode_string(original_title),
                year)
    log(u'name is {}'.format(name))
    playing_strm = make_path_to_base_relative(u'Movies/' + name + u'.strm')
    save_strm(playing_strm, play_url, sort_index)
    return name

def get_movies_by(dirname, filename, fields=["file"]):
    filter = find_file_filter(dirname, filename)

    from vdlib.kodi.jsonrpc_requests import VideoLibrary
    result = VideoLibrary.GetMovies(filter=filter, properties=fields)    
    return result

def set_movie_resume_playcount(movieid, player_video_info):
    # type: (int, PlayerVideoInfo) -> None
    from vdlib.kodi.jsonrpc_requests import VideoLibrary
    percent = player_video_info.time / player_video_info.total_time * 100
    if player_video_info.time > 180:
        if percent < 90:
            resume = {'position': player_video_info.time,
                         'total': player_video_info.total_time}
            result = VideoLibrary.SetMovieDetails(movieid=movieid,resume=resume)
        else:
            result = VideoLibrary.SetMovieDetails(movieid=movieid,playcount=1)
    pass

def update_library(path=None, on_update=None):
    import xbmc

    class MyMonitor(xbmc.Monitor):
        def onScanFinished(self, library):
            if callable(on_update) and on_update():
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

    log(u'def save_strm(file_path, play_url)')
    log(u'file_path is "{}"'.format(file_path))

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

def save_tvshow(player_video_info):
    # type: (PlayerVideoInfo) -> None
    video_info = player_video_info.video_info
    original_title = video_info.get('originaltitle')
    year = video_info.get('year')
    imdb = video_info.get('imdbnumber')
    hash = Engine.extract_hash_from_play_url(player_video_info.play_url)
    if original_title and year:
        from .info import add_tvshows_to_lib
        if add_tvshows_to_lib():
            save_tvshow.playing_strm = None
            def episode_func(filename, play_url):
                if play_url == player_video_info.play_url:
                    save_tvshow.playing_strm = filename
                log(hash)
        
            ts_engine = Engine(hash=hash, host=ts_settings.host, port=ts_settings.port, auth=ts_settings.auth)
            save_tvshow_strms(video_info.get('title'), original_title, year, imdb, ts_engine, episode_func=episode_func)

            part_dirname = filesystem.join('TVShows', get_tvshow_dirname(original_title, year))
            tvshow_path = make_path_to_base_relative(part_dirname)

            def on_update_library():
                if not save_tvshow.playing_strm:
                    return True

                result = get_episodes_by(part_dirname, save_tvshow.playing_strm)
                episodes = result.get('episodes')
                if episodes:
                    episode = episodes[0]
                    set_episode_resume_playcount(episode['episodeid'], player_video_info)

                return True

            update_library(tvshow_path, on_update_library)


def save_tvshow_strms(title, original_title, year, imdb, ts_engine, episode_func=None, ts_stat=None):
    # type (str, str, str, str, Engine, (str, str) -> None, dict) -> None
    from vdlib.util import filesystem
    tvshow_dirname = get_tvshow_dirname(original_title, year)

    part_dirname = filesystem.join('TVShows', tvshow_dirname)
    tvshow_path = make_path_to_base_relative(part_dirname)
    if not filesystem.exists(tvshow_path):
        filesystem.makedirs(tvshow_path)

    from vdlib.scrappers.tvshowapi import TVShowAPI, parse_torrent
    api = TVShowAPI(original_title, title, imdb)

    if not ts_stat:
        ts_stat = ts_engine.stat()
    info = {'name': ts_stat.get('Name'), 
            'files': []}
    ts_engine_files = ts_engine.files(ts_stat)
    for f in ts_engine_files:
        path = f['path'].split('/')
        info['files'].append({'path': path})

    files = parse_torrent(info)
    for item in files:
        if not api.Episode(item['season'], item['episode']):
            continue

        season_path = filesystem.join(tvshow_path, u'Season {}'.format(item['season']))
        if not filesystem.exists(season_path):
            filesystem.makedirs(season_path)
        filename = u'{} ({}) S{:02d}E{:02d}.strm'.format(original_title, year, item['season'], item['episode'])
        sort_index = item['index']
        play_url = ts_engine.play_url(sort_index, torrent_stat=ts_stat)
        strm_path = filesystem.join(season_path, filename)
        save_strm(strm_path, play_url, sort_index)
        if episode_func:
            episode_func(filename, play_url)


def get_tvshow_dirname(original_title, year):
    tvshow_dirname = u'{} ({})'.format(original_title, year)
    log(tvshow_dirname)
    return tvshow_dirname


def get_episodes_by(dirname, filename, fields=["file"]):
    filter = find_file_filter(dirname, filename)

    from vdlib.kodi.jsonrpc_requests import VideoLibrary
    result = VideoLibrary.GetEpisodes(filter=filter, properties=fields)    
    return result


def set_episode_resume_playcount(episodeid, player_video_info):
    # type: (int, PlayerVideoInfo) -> None
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