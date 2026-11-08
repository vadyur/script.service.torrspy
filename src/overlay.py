# -*- coding: utf-8 -*-

'''Оверлей TorrServer, показываемый на паузе.

Вынесен в отдельный модуль: RunScript запускается на каждое событие паузы, и импорт
src.script (vdlib -> requests/urllib3) стоил на SHIELD ~2,5 с. Пауза длительностью
4 с не успевала показать оверлей. Здесь импортируются только xbmc/xbmcgui и
torrserve_stream.overlay.
'''

import xbmc
import xbmcgui

from typing import Any, Optional, Tuple

# Сколько ждём подтверждения паузы: Kodi обрабатывает pause() асинхронно, и на момент
# старта скрипта скорость воспроизведения ещё может быть ненулевой.
PAUSE_CONFIRM_TIMEOUT: float = 2.0
PAUSE_CONFIRM_STEP: float = 0.2


def log(s: str) -> None:
    from vdlib.torrspy import _unit_log
    _unit_log('overlay.py', s)


def show_overlay_on_pause(hash: str, index: Optional[str]) -> None:
    from time import time
    from torrserve_stream.overlay import Overlay

    class SpyPlayer(xbmc.Player):
        def __init__(self) -> None:
            super().__init__()
            self.paused: bool = True

        def onPlayBackEnded(self) -> None:
            self.paused = False

        def onPlayBackStopped(self) -> None:
            self.paused = False

        def onPlayBackError(self) -> None:
            self.paused = False

        def onPlayBackPaused(self) -> None:
            self.paused = True

        def onPlayBackResumed(self) -> None:
            self.paused = False

        def state(self) -> Tuple[bool, bool, bool]:
            return self.isPlayingVideo(), xbmc.getCondVisibility('Player.Paused'), self.paused

        def isPaused(self) -> bool:
            playing, cond, flag = self.state()
            return playing and cond and flag

    started: float = time()

    window = xbmcgui.Window(12005)
    if window.getProperty('torrserve_overlay_active') == '1':
        log('overlay skipped: TorrServer overlay already active')
        return

    player = SpyPlayer()
    monitor = xbmc.Monitor()
    overlay: Optional[Any] = None

    try:
        # Ждём подтверждённой паузы: событие паузы уже произошло (нас запустил сервис),
        # но RunScript + интерпретатор Python дают свою задержку, и Player.Paused
        # (== IsPlaying() && GetPlaySpeed() == 0) устанавливается не мгновенно.
        deadline = started + PAUSE_CONFIRM_TIMEOUT
        while not player.isPaused():
            playing, cond, flag = player.state()
            if not playing:
                log('overlay skipped: no video playback (cond={} flag={})'.format(cond, flag))
                return
            if monitor.waitForAbort(PAUSE_CONFIRM_STEP):
                return
            if time() > deadline:
                log('overlay skipped: pause not confirmed (cond={} flag={})'.format(cond, flag))
                return

        idx = int(index) if index else None
        # Вторая проверка: два RunScript на одну паузу могли стартовать почти одновременно,
        # и свой оверлей появился, пока мы подтверждали паузу.
        if window.getProperty('torrserve_overlay_active') == '1':
            log('overlay skipped: TorrServer overlay became active')
            return

        overlay = Overlay(hash=hash, index=idx)

        overlay.show()
        log('overlay shown {:.2f} s after start'.format(time() - started))

        while not monitor.abortRequested():
            # Player.Paused здесь не используем: на баффере и после seek он мигает в False
            if not player.paused or not player.isPlayingVideo():
                break
            overlay.update()
            if monitor.waitForAbort(0.8):
                break
    finally:
        if overlay:
            overlay.hide()
