# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcaddon

from sys import version_info
from time import time
from typing import Any, Dict, Optional

if version_info >= (3, 0, 0):
    from urllib.parse import quote_plus
else:
    from urllib import quote_plus   #type: ignore

from .links import is_torrserver_url
from .pause_overlay import PauseOverlay, OVERLAY_TICK
from .pause_restore import PauseRestorer

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_path = addon.getAddonInfo('path')

def log(s: str) -> None:
    from vdlib.torrspy import _unit_log
    _unit_log('service.py', s)

def make_url(action: Optional[str]) -> str:
    if action:
        params_str = quote_plus(action)
        url = 'plugin://{}/{}'.format(addon_id, params_str)
    else:
        url = 'plugin://{}'.format(addon_id)
    return url

def RunPlugin(action: Optional[str]) -> None:
    import xbmc
    url = make_url(action)
    xbmc.executebuiltin('RunPlugin("%s")' % url)

def RunScript(*args: Any) -> None:
    import xbmc, os

    path = addon_id # os.path.join(addon_path, 'script.py')
    args = [ str(i) for i in args ]
    param_str = ', '.join(args)
    xbmc.executebuiltin('RunScript({}, {})'.format(path, param_str))

def Test() -> None:
    # testing
    RunPlugin("run")

class MyMonitor(xbmc.Monitor):

    def onSettingsChanged(self) -> None:
        pass

# updateInfoTag() на потоке, стоящем на паузе, даёт respawn: воспроизведение продолжается
# (в логе - CDVDAudio::Resume + OnPlayBackStarted спустя ~3 с). Восстановлением паузы
# занимается PauseRestorer (src/pause_restore.py).
SERVICE_TICK = 2


def start_external_video_info(player: 'MyPlayer', url: Optional[str]) -> None:
    """Видео запущено извне: запомнить это, снять маркер TorrSpy и запустить получение информации."""

    paused = xbmc.getCondVisibility('Player.Paused')
    player.pause_overlay.mark_external(url)
    log('reset tagline')

    item = xbmcgui.ListItem()
    item.setPath(url)
    item.setInfo('video', {'tagline': ''})   # type: ignore
    player.updateInfoTag(item)

    if paused:
        player.pause_restorer.arm()

    log('RunScript get_info')
    RunScript('get_info')
    RunScript('seek_saved_pos')


class MyPlayer(xbmc.Player):

    tagline: str = '##TorrSpy##'

    def __init__(self) -> None:
        player_video_started = time()
        from vdlib.torrspy.player_video_info import PlayerVideoInfo
        log('PlayerVideoInfo import in {:.2f} s'.format(time() - player_video_started))

        self.video_info: Any = PlayerVideoInfo(self)
        self.hash: Optional[str] = None
        self.index: Optional[int] = None
        self.pause_overlay: PauseOverlay = PauseOverlay(self, log)
        self.pause_restorer: PauseRestorer = PauseRestorer(self, log)
        # до xbmc.Player.__init__(): onAVStarted может прийти сразу после регистрации плеера
        self.av_started_for: Optional[str] = None

        xbmc_started = time()
        xbmc.Player.__init__(self)
        log('xbmc.Player init in {:.2f} s'.format(time() - xbmc_started))

    def getVideoInfo(self) -> Dict[str, Any]:
        tag = self.getVideoInfoTag()

        result: Dict[str, Any] = {}

        if not self.isPlayingVideo():
            return result

        def _is_string_type(s: Any) -> bool:
            if isinstance(s, str):
                return True
            elif version_info < (3, 0) and isinstance(s, unicode):  # type: ignore
                return True
            return False

        def _integer(i: Any) -> int:
            return int(i)

        def _string_or_list_of_strings(s: Any) -> Any:
            if _is_string_type(s) and ',' in s:
                return s.split(',')
            return s

        def _string(s: Any) -> str:
            return s

        def _list(l: Any) -> Any:
            if _is_string_type(l):
                return l.split(',')
            return l

        def _float(f: Any) -> float:
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

    def onPlayBackStarted(self) -> None:
        log('MyPlayer.onPlayBackStarted')

    def onAVStarted(self) -> None:
        from torrserve_stream.engine import Engine
        log('MyPlayer.onAVStarted')

        tag = self.getVideoInfoTag()
        file: Optional[str] = self.getPlayingFile()

        # Kodi сам присылает onAVStarted xbmc.Player(), созданному во время активного
        # воспроизведения, поэтому ручной вызов из main() не должен повторять обработку.
        if file and file == self.av_started_for:
            log('\t{} already handled'.format(file))
            return
        self.av_started_for = file

        log('\tMyPlayer.file = {}'.format(file))
        log('\tMyPlayer.getTitle() = {}'.format(tag.getTitle()))
        log('\tMyPlayer.DbId = {}'.format(tag.getDbId()))

        if file:
            self.hash = Engine.extract_hash_from_play_url(file)
            self.index = Engine.extract_file_index_from_play_url(file)
            log('\thash={} index={}'.format(self.hash, self.index))

        if tag.getOriginalTitle() or tag.getDbId() > 0:
            log('Keep current info')
            return

        # Видео без информации, запущенное извне: получаем информацию сразу, не дожидаясь цикла сервиса
        # (раньше ставился маркер TorrSpy в tagline, и цикл подхватывал его только через 2-4 секунды)
        if tag.getTagLine() == self.tagline or is_torrserver_url(file):
            start_external_video_info(self, file)

    def show_pause_overlay(self, reason: str) -> None:
        self.pause_overlay.show(reason, self.hash, self.index)

    def hide_pause_overlay(self, reason: str) -> None:
        self.pause_overlay.hide(reason)

    def update_pause_overlay(self) -> None:
        self.pause_overlay.update()

    def onPlayBackPaused(self) -> None:
        url: Optional[str] = None
        try:
            url = self.getPlayingFile()
        except RuntimeError:
            url = None
        external = self.pause_overlay.is_external(url)
        log('MyPlayer.onPlayBackPaused hash={} index={} external={}'.format(self.hash, self.index, external))
        self.show_pause_overlay('onPlayBackPaused')

    def onPlayBackResumed(self) -> None:
        log('MyPlayer.onPlayBackResumed')
        self.hide_pause_overlay('onPlayBackResumed')

    def onPlayBackStopped(self) -> None:
        log('MyPlayer.onPlayBackStopped')
        self.end_playback()

    def onPlayBackEnded(self) -> None:
        log('MyPlayer.onPlayBackEnded')
        self.end_playback()

    def onPlayBackError(self) -> None:
        log('MyPlayer.onPlayBackError')
        self.hide_pause_overlay('onPlayBackError')

    def onPlayBackSeek(self, time: float, seekOffset: float) -> None:
        log('MyPlayer.onPlayBackSeek time={} seekOffset={}'.format(time, seekOffset))

    def onPlayBackSpeedChanged(self, speed: float) -> None:
        log('MyPlayer.onPlayBackSpeedChanged speed={}'.format(speed))

    def end_playback(self) -> None:
        self.hide_pause_overlay('end_playback')
        RunScript('end_playback', self.video_info.dumps())
        self.video_info.reset()
        self.pause_overlay.clear()
        self.pause_restorer.clear()

def main() -> None:

    log('--- Start TorrSpy service ---')

    monitor: MyMonitor = MyMonitor()
    # "уже играет" проверяем этим же MyPlayer: отдельный xbmc.Player() из playing_torrserver_source()
    # блокируется на очереди событий плеера на секунды и забирает событие паузы себе.
    player_created: float = time()
    player: MyPlayer = MyPlayer()
    log('MyPlayer created in {:.2f} s'.format(time() - player_created))

    probe_started: float = time()
    start_url: Optional[str] = None
    try:
        if player.isPlayingVideo():
            start_url = player.getPlayingFile()
    except RuntimeError:
        start_url = None

    is_player_already_playing: bool = is_torrserver_url(start_url)
    log('startup probe in {:.2f} s'.format(time() - probe_started))

    if is_player_already_playing:
        log('Player is already playing TorrServer stream')
        # Player.Paused читаем до onAVStarted(): start_external_video_info() вызывает
        # updateInfoTag(), а это respawn, который снимает паузу.
        paused_at_start: bool = xbmc.getCondVisibility('Player.Paused')
        player.onAVStarted()
        log('Startup paused={} hash={} index={}'.format(paused_at_start, player.hash, player.index))

        if paused_at_start and xbmc.getCondVisibility('Player.Paused'):
            log('Player already paused at startup, calling onPlayBackPaused')
            player.onPlayBackPaused()

    schedule_add_all_from_torserver_last_run: float = time()

    position_save_interval: int = 30
    last_position_save: float = time()
    last_play_url: Optional[str] = None

    while not monitor.abortRequested():
        if monitor.waitForAbort(OVERLAY_TICK if player.pause_overlay.active else SERVICE_TICK):
            break

        now: float = time()
        if now > schedule_add_all_from_torserver_last_run + 30:
            RunScript('schedule_add_all_from_torserver')
            schedule_add_all_from_torserver_last_run = now

        # оверлей активен только на паузе: PauseOverlay обновляет счётчики и прячет его,
        # если пауза снята без колбэка
        player.update_pause_overlay()

        if player.pause_restorer.pending:
            if player.isPlaying():
                player.pause_restorer.restore()
            else:
                player.pause_restorer.clear()
            continue

        if player.pause_overlay.active:
            continue

        if not player.isPlaying():
            continue

        try:
            current_play_url: Optional[str] = player.getPlayingFile()
        except RuntimeError:
            log('getPlayingFile RuntimeError')
            continue

        # тот же плеер, что и в колбэках: xbmc.Player() на каждой итерации лишним плодит
        # ещё одну регистрацию и забирает себе события
        if not is_torrserver_url(current_play_url):
            continue

        try:
            vit: Any = player.getVideoInfoTag()
        except RuntimeError:
            log('getVideoInfoTag RuntimeError')
            continue

        player.video_info.update()

        if current_play_url != last_play_url:
            log('Video changed: {} -> {}'.format(last_play_url, current_play_url))
            last_play_url = current_play_url
            last_position_save = time()

        now = time()

        if now >= last_position_save + position_save_interval:
            log('Saving playback position')

            try:
                RunScript(
                    'save_playback_position',
                    player.video_info.dumps()
                )
            except Exception as e:
                log(
                    'Error saving playback position: {}'.format(
                        str(e)
                    )
                )

            last_position_save = now

        if vit.getTagLine() == player.tagline:
            start_external_video_info(player, current_play_url)

    player.hide_pause_overlay('service stop')
