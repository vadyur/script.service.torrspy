# -*- coding: utf-8 -*-

import xbmc

from time import time
from typing import Any, Callable, Dict, Optional

RESTORE_PAUSE_DELAY = 4
RESTORE_PAUSE_TIMEOUT = 20
RESTORE_PAUSE_ATTEMPTS = 3


class PauseRestorer:
    def __init__(self, player: xbmc.Player, log: Callable[[str], None]) -> None:
        self.player = player
        self.log = log
        self.state: Optional[Dict[str, Any]] = None

    @property
    def pending(self) -> bool:
        return self.state is not None

    def arm(self) -> None:
        now = time()
        self.state = {
            'until': now + RESTORE_PAUSE_TIMEOUT,
            'not_before': now + RESTORE_PAUSE_DELAY,
            'attempts': 0,
        }
        self.log('video was paused: pause will be restored after info update')

    def clear(self) -> None:
        self.state = None

    def restore(self) -> None:
        state = self.state
        if state is None:
            return

        if xbmc.getCondVisibility('Player.Paused'):
            self.log('pause is back')
            self.clear()
            return

        now = time()
        if now > state['until'] or state['attempts'] >= RESTORE_PAUSE_ATTEMPTS:
            self.log('pause not restored after info update')
            self.clear()
            return

        if now < state['not_before']:
            return

        try:
            speed = self.player.getPlaySpeed()
        except Exception:
            speed = None

        if self.player.isPlayingVideo() and (speed is None or speed != 0):
            state['attempts'] += 1
            state['not_before'] = now + RESTORE_PAUSE_DELAY
            self.log('restoring pause (attempt {})'.format(state['attempts']))
            self.player.pause()
