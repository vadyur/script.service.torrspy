# -*- coding: utf-8 -*-

import re, os

videoextensions = [
    '.m4v', '.3g2', '.3gp', '.nsv', '.tp', '.ts', '.ty', '.strm', '.pls', '.rm', '.rmvb', '.mpd', '.m3u', '.m3u8', '.ifo', '.mov', '.qt', '.divx', '.xvid',
    '.bivx', '.vob', '.nrg', '.img', '.iso', '.udf', '.pva', '.wmv', '.asf', '.asx', '.ogm', '.m2v', '.avi', '.bin', '.dat', '.mpg', '.mpeg', '.mp4',
    '.mkv', '.mk3d', '.avc', '.vp3', '.svq3', '.nuv', '.viv', '.dv', '.fli', '.flv', '.001', '.wpl', '.xspf', '.zip', '.vdr', '.dvr-ms', '.xsp', '.mts',
    '.m2t', '.m2ts', '.evo', '.ogv', '.sdp', '.avs', '.rec', '.url', '.pxml', '.vc1', '.h264', '.rcv', '.rss', '.mpls', '.mpl', '.webm', '.bdmv',
    '.bdm', '.wtv', '.trp', '.f4v'
]

cleandatetime = r'(.*[^ _\,\.\(\)\[\]\-])[ _\.\(\)\[\]\-]+(19[0-9][0-9]|20[0-9][0-9])([ _\,\.\(\)\[\]\-]|[^0-9]$)?'

cleanstrings = [
   r'[ _\,\.\(\)\[\]\-](ac3|dts|custom|dc|remastered|divx|divx5|dsr|dsrip|dutch|dvd|dvd5|dvd9|dvdrip|dvdscr|dvdscreener|screener|dvdivx|cam|fragment|fs|hdtv|hdrip|hdtvrip|internal|limited|multisubs|ntsc|ogg|ogm|pal|pdtv|proper|repack|rerip|retail|r3|r5|bd5|se|svcd|swedish|german|read.nfo|nfofix|unrated|extended|ws|telesync|ts|telecine|tc|brrip|bdrip|480p|480i|576p|576i|720p|720i|1080p|1080i|3d|hrhd|hrhdtv|hddvd|bluray|x264|h264|xvid|xvidvd|xxx|www.www|cd[1-9]|\[.*\])([ _\,\.\(\)\[\]\-]|$)',
   r'(\[.*\])',
]

def is_video(filename):
    for ext in videoextensions:
        if filename.endswith(ext):
            return True
    return False

def extract_title_date(filename):
    title = filename

    m = re.search(cleandatetime, title)
    title = m.group(1) if m else title
    date = m.group(2) if m else None

    for clinning_re in cleanstrings:
        m = re.search(clinning_re, title)
        if m:
            title = title.replace(m.group(1), '')

    if '[' in title:
        title = title.split('[')[0]

    title = title.replace('.', ' ').strip()

    return title, date

def extract_original_title_year(title):
    source = title
    year = None
    original_title = None
    if '/' in source:
        parts = source.split('/')
        title = parts[0]

        original_title = None

        m = re.search(r'/ (19[0-9][0-9]|20[0-9][0-9]) /', source)
        if m:
            year = m.group(1)
            parts = source.split(m.group(0))[0]
            parts = parts.split('/')
            original_title = parts[-1]
        else:
            for part in reversed(parts[1:]):
                m = re.search(r'(19[0-9][0-9]|20[0-9][0-9])', part.strip())
                if m:
                    original_title, year = extract_title_date(part)
                    if original_title and year:
                        break
                    year = m.group(1)

    video_info = {'title': title.strip()}
    if original_title:
        if not year:
            original_title, year = extract_title_date(original_title.strip())
        video_info['originaltitle'] = original_title.strip()
    if year:
        video_info['year'] = year
    return video_info

def extract_filename(url):
    from torrserve_stream.engine import Engine
    return Engine.extract_filename_from_play_url(url)

def from_translit(text):
    from transliterate import translit, detect_language
    l = detect_language(text)
    r = translit(text, 'ru')
    return r

def test(url):
    n = extract_filename(url)
    t, d = extract_title_date(n)
    r = from_translit(t)

    return n, t, d, r

def find_tmdb_movie_item(video_info):
    from vdlib.scrappers.movieapi import TMDB_API, tmdb_movie_item
    tmdb = TMDB_API()
    original_title = video_info.get('originaltitle')
    if original_title:
        results = tmdb.search(original_title)
        if len(results) == 1:
            result = results[0]     # type: tmdb_movie_item
            return result

        filters = [
            'originaltitle',
            'plot',
            'year',
            'title'
        ]

        for field in filters:
            def filter_func(res):
                info = res.get_info()
                return info.get(field) == video_info.get(field)
            if field in video_info:
                filtered = list(filter(filter_func, results))
                if len(filtered) == 1:
                    results = filtered
                    break

        if len(results):
            result = results[0] # type: tmdb_movie_item
            return result

if __name__ == '__main__':
    from unittest import TestCase, main

    class TestDetect(TestCase):
        def test_01(self):
            s = u'Невероятные / The Nevers [S01] (2021) WEBRip 1080p от Kerob | L2 | The.Nevers.S01.1080p.Kerob'
            r = extract_original_title_year(s)
            self.assertEqual(r['title'], u'Невероятные')
            self.assertEqual(r['originaltitle'], u'The Nevers')
            self.assertEqual(r['year'], u'2021')

        def test_02(self):
            s = u'Полный нокдаун / American Fighter / 2019 / ДБ / BDRip (1080p) | American.Fighter.2019.BDRip.1080p.seleZen.mkv'
            r = extract_original_title_year(s)
            self.assertEqual(r['title'], u'Полный нокдаун')
            self.assertEqual(r['originaltitle'], u'American Fighter')
            self.assertEqual(r['year'], u'2019')

        def test_03(self):
            s = u'Берег москитов / The Mosquito Coast [01x01-04 из 07] (2021) WEB-DL 1080p | AlexFilm | The_Mosquito_Coast_(s01)_AlexFilm_1080p'
            r = extract_original_title_year(s)
            self.assertEqual(r['title'], u'Берег москитов')
            self.assertEqual(r['originaltitle'], u'The Mosquito Coast')
            self.assertEqual(r['year'], u'2021')

        def test_04(self):
            s = u'Мастер меча / Мечник / Geomgaek / The Swordsman (2020) HDRip-AVC от MediaBit | iTunes'
            r = extract_original_title_year(s)
            self.assertEqual(r['title'], u'Мастер меча')
            self.assertEqual(r['originaltitle'], u'The Swordsman')
            self.assertEqual(r['year'], u'2020')

        '''
        def test_(self):
            s = u''
            r = extract_original_title_year(s)
            self.assertEqual(r['title'], u'')
            self.assertEqual(r['originaltitle'], u'')
            self.assertEqual(r['year'], u'')
        '''

    main()
