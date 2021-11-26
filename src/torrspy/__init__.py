from .strm_utils import save_movie_strm, save_tvshow_strms

def _unit_log(unit, s):
    from .info import addon_id
    try:
        message = u'[{}: {}]: {}'.format(addon_id, unit, s)
    except UnicodeDecodeError:
        message = u'[{}: {}]: {}'.format(addon_id, unit, s.decode('utf-8'))

    import xbmc
    try:
        xbmc.log(message)
    except UnicodeEncodeError:
        xbmc.log(message.encode('utf-8'))
