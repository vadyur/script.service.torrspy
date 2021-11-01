# -*- coding: utf-8 -*-

import re

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
    # type: (str) -> bool
    for ext in videoextensions:
        if filename.endswith(ext):
            return True
    return False

def is_episode(filename):
    # type: (str) -> bool
    pattern = r'[s|S]\d+[e|E]\d+'
    return True if re.search(pattern, filename) else False

def extract_title_date(filename):
    # type: (str) -> tuple
    title = filename

    m = re.search(cleandatetime, title)
    if m:
        title = m.group(1)
        date = m.group(2)
    else:        
        date = None

    for clinning_re in cleanstrings:
        m = re.search(clinning_re, title)
        if m:
            title = title.replace(m.group(1), '')

    if date:
        for date_part in [ '['+date+']', '('+date+')' ]:
            if date_part in title:
                title = title.split(date_part)[0]

    if '[' in title:
        title = title.split('[')[0]

    title = title.replace('.', ' ').strip()

    return title, date

def validate_part(part):
    keys =  [u'Сезон', u'Серии', u'сезон', u'серии']
    for key in keys:
        if key in part:
            return False

    if re.search(u'\\d из \\d', part):
        return False

    return True

def clean_part(part):
    part = re.sub(r'\[.+?\]', '', part)
    #part = re.sub(r'\(.+?\)', part)
    return part.strip()

def clean_title(part):
    part = clean_part(part)
    part = re.sub(r'\(.+?\)', '', part)
    return part.strip()

def _extract_KT_title_year(title):
    pattern = r'\[KT\] (.+) \((19[0-9][0-9]|20[0-9][0-9])\)'
    m = re.match(pattern, title)
    if m:
        return { 'title': m.group(1), 'year': m.group(2) }

def _find_date_period(source):
    m = re.search(r'/ (19[0-9][0-9]|20[0-9][0-9])\s*-\s*(19[0-9][0-9]|20[0-9][0-9]) /', source)    
    if m:
        return m.group(1), m.group(2)

def extract_original_title_year(title):
    source = title
    year = None
    original_title = None

    video_info = _extract_KT_title_year(title)
    if video_info:
        return video_info

    if '/' in source:
        parts = source.split('/')
        title = clean_title(parts[0])
        parts[0] = title

        parts = [ clean_part(part) for part in parts ]
        parts = list(filter(validate_part, parts))

        original_title = parts[1] if len(parts) >= 2 else None

        m = re.search(r'/ (19[0-9][0-9]|20[0-9][0-9]) /', source)
        if m:
            year = m.group(1)
            parts = source.split(m.group(0))[0]
            parts = parts.split('/')
            original_title = parts[-1]
        elif _find_date_period(source):
            year = _find_date_period(source)[0]
        else:
            for part in reversed(parts[1:]):
                m = re.search(r'(19[0-9][0-9]|20[0-9][0-9])', part.strip())
                if m:
                    original_title, year = extract_title_date(part)
                    if original_title and year:
                        break
                    year = m.group(1)

    if not year:
        m = re.search(r'(19[0-9][0-9]|20[0-9][0-9])', source)
        if m:
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

    def find_by(title):
        results = tmdb.search(title)
        if len(results) == 1:
            result = results[0]     # type: tmdb_movie_item
            return result

        def str_func(tmdb, loc):
            return tmdb == loc

        def date_func(tmdb, loc):
            return str(tmdb) == str(loc)

        filters = {
            'originaltitle': str_func,
            'plot': str_func,
            'year': date_func,
            'title': str_func
        }

        for field in filters:
            def filter_func(res):
                tmdb_info = res.get_info()
                return filters[field](tmdb_info.get(field), video_info.get(field))
            if field in video_info:
                filtered = list(filter(filter_func, results))
                if len(filtered) == 1:
                    results = filtered
                    break

        if len(results):
            result = results[0] # type: tmdb_movie_item
            return result

    for field in ['originaltitle', 'title']:
        title = video_info.get(field)
        if title:
            result = find_by(title)
            if result:
                return result

