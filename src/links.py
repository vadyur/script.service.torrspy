# -*- coding: utf-8 -*-

import re
from typing import Any, Optional

_ts_settings_cache: Optional[Any] = None


def _ts_settings() -> Any:
    global _ts_settings_cache
    if _ts_settings_cache is None:
        from torrserve_stream.settings import Settings
        _ts_settings_cache = Settings()
    return _ts_settings_cache


def is_torrserve_v2_link(url: Optional[str]) -> bool:
    pattern = r'http://.+/stream/.+\?link=[a-f\d]{40}&index=\d+&play'
    return url is not None and re.match(pattern, url) is not None


def is_torrserve_v1_link(url: Optional[str]) -> bool:
    pattern = r'http://.+/torrent/view/[a-f\d]{40}/'
    return url is not None and re.match(pattern, url) is not None


def is_torrserver_url(url: Optional[str]) -> bool:
    if not url:
        return False

    if is_torrserve_v2_link(url) or is_torrserve_v1_link(url):
        return True

    return ':{}/'.format(_ts_settings().port) in url


def playing_torrserver_source() -> bool:
    import xbmc
    player = xbmc.Player()

    if player.isPlayingVideo():
        return is_torrserver_url(player.getPlayingFile())

    return False
