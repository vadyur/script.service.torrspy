# -*- coding: utf-8 -*-

import json

import xbmc
import xbmcaddon
import xbmcgui

from vdlib.util.string import decode_string
from vdlib.util import filesystem

addon = xbmcaddon.Addon('script.service.torrspy')
addon_id = addon.getAddonInfo('id')

def addon_title():
    return addon.getAddonInfo('name')

def addon_setting(id):
    return addon.getSetting(id)

def addon_set_setting(id, value):
    log('{} set to {}'.format(id, value))    
    addon.setSetting(id, value)

def addon_base_path():
    base_path = addon_setting('base_path')
    return base_path

def add_all_from_torserver():
    # type: () -> bool
    return addon_setting('add_all_from_torserver') == 'true'

# спросить|автоматически|нет
def add_movies_to_lib():
    s = decode_string(addon_setting('add_movies_to_lib'))

    if s == u'автоматически':
        return True

    if s == u'нет':
        return False

    return xbmcgui.Dialog().yesno(addon_title(), 
            u'Кино не досмотрено. Сохранить его в медиатеку для последующего просмотра?')

def add_tvshows_to_lib():
    s = decode_string(addon_setting('add_tvshows_to_lib'))

    if s == u'автоматически':
        return True

    if s == u'нет':
        return False

    return xbmcgui.Dialog().yesno(addon_title(), 
            u'Вы смотрели эпизод сериала. Сохранить сериал в медиатеку для последующего просмотра?')


def make_path_to_base_relative(path):
    return filesystem.join(addon_base_path(), path)

def log(s):
    from . import _unit_log
    _unit_log('info.py', s)

def save_video_info(hash, video_info):
    if 'imdbnumber' not in video_info:
        return

    log('---TorrSpy: save_info---')

    with filesystem.fopen(get_video_info_path(hash, create_path=True), 'w') as vi_out: 
        try:
            json.dump(video_info, vi_out, indent=4, ensure_ascii=False)
        except UnicodeEncodeError:
            json.dump(video_info, vi_out, indent=4)

def save_art(hash, art):
    if art:
        with filesystem.fopen(get_art_path(hash, create_path=True), 'w') as a_out:
            try:
                json.dump(art, a_out, indent=4, ensure_ascii=False)
            except UnicodeEncodeError:
                json.dump(art, a_out, indent=4)

def get_art_path(hash, create_path=False):
    path = make_path_to_base_relative('.data')
    if create_path and not filesystem.exists(path):
        filesystem.makedirs(path)
    filename = '{}.art.json'.format(hash)
    return filesystem.join(path, filename)

def get_video_info_path(hash, create_path=False):
    path = make_path_to_base_relative('.data')
    if create_path and not filesystem.exists(path):
        filesystem.makedirs(path)
    filename = '{}.video_info.json'.format(hash)
    return filesystem.join(path, filename)

def load_video_info(hash):
    video_info_path = get_video_info_path(hash)
    if filesystem.exists(video_info_path):
        with filesystem.fopen(video_info_path, 'r') as vi_in:
            return json.load(vi_in)

def load_art(hash):
    art_path = get_art_path()
    if filesystem.exists(art_path):
        with filesystem.fopen(art_path, 'r') as a_in:
            return json.load(a_in)