# -*- coding: utf-8 -*-

import xbmc
import xbmcgui

from time import time
from typing import Any, Callable, Dict, Optional

OVERLAY_TICK: int = 1
PAUSE_HIDE_TICKS: int = 2


class PauseOverlay:
    """Оверлей TorrServer на паузе.

    Живёт в процессе TorrSpy service. Отдельный файл нужен, чтобы service.py
    содержал только тонкие вызовы show/hide/update, а логику оверлея можно было
    менять и тестировать независимо.
    """

    def __init__(self, player: xbmc.Player, log: Callable[[str], None]) -> None:
        self.player = player
        self.log = log
        self.overlay: Optional[Any] = None
        self.paused_ticks: int = 0
        # url воспроизведения -> True, если видео запущено извне (торрспай снял свой маркер)
        self.external: Dict[str, bool] = {}

    @property
    def active(self) -> bool:
        return self.overlay is not None

    def mark_external(self, url: Optional[str]) -> None:
        if url:
            self.external[url] = True

    def is_external(self, url: Optional[str]) -> bool:
        return bool(url) and self.external.get(url, False)

    def clear(self) -> None:
        self.external.clear()

    def _allowed(self, torrent_hash: Optional[str]) -> bool:
        if not torrent_hash:
            return False

        try:
            url = self.player.getPlayingFile()
        except RuntimeError:
            return False

        if not self.is_external(url):
            return False

        if xbmcgui.Window(12005).getProperty('torrserve_overlay_active') == '1':
            self.log('overlay skipped: TorrServer overlay already active')
            return False

        return True

    def show(self, reason: str, torrent_hash: Optional[str], index: Optional[int]) -> None:
        if self.active:
            return

        if not self._allowed(torrent_hash):
            return

        started = time()
        try:
            from torrserve_stream.overlay import Overlay
            overlay = Overlay(hash=torrent_hash, index=index)
            overlay.show()
        except Exception as e:
            self.log('overlay show failed ({}): {}'.format(reason, str(e)))
            return

        self.overlay = overlay
        self.paused_ticks = 0
        self.log('overlay shown on pause ({}), {:.2f} s'.format(reason, time() - started))

    def hide(self, reason: str) -> None:
        if not self.active:
            return

        try:
            self.overlay.hide()
        except Exception as e:
            self.log('overlay hide failed ({}): {}'.format(reason, str(e)))

        self.overlay = None
        self.log('overlay hidden: {}'.format(reason))

    def update(self) -> None:
        if not self.active:
            return

        if not self.player.isPlayingVideo():
            self.hide('playback stopped')
            return

        if xbmc.getCondVisibility('Player.Paused'):
            self.paused_ticks = 0
        else:
            # Player.Paused мигает в False на баффере и после seek, поэтому скрываем не по одному False
            self.paused_ticks += 1
            if self.paused_ticks >= PAUSE_HIDE_TICKS:
                self.hide('resumed')
                return

        try:
            self.overlay.update()
        except Exception as e:
            self.log('overlay update failed: {}'.format(str(e)))
