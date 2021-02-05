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

def extract_title_date(filename):
    title = filename
    for ext in videoextensions:
        if filename.endswith(ext):
            title = os.path.splitext(filename)[0]
            break
    if filename == title:
        return None

    m = re.search(cleandatetime, title)
    title = m.group(1) if m else title
    date = m.group(2) if m else None

    for clinning_re in cleanstrings:
        m = re.search(clinning_re, title)
        if m:
            title = title.replace(m.group(1), '')

    title = title.replace('.', ' ').strip()

    return title, date

def extract_filename(url):
    import re
    pattern = r'/stream/(.+)\?link='
    m = re.search(pattern, url)
    if m:
        return m.group(1)

def from_translit(text):
    from transliterate import translit, detect_language
    l = detect_language(text)
    r = translit(text, 'ru')
    return r

def test():
    u = 'http://127.0.0.1:8090/stream/Drozh.zemli.Ostrov.krikunov.2020.BDRip.1080p.ELEKTRI4KA.UNIONGANG.mkv?link=b1cd1ebbe7cd7317beb91575f9b0473a87b2baa7&index=1&play'
    n = extract_filename(u)
    t, d = extract_title_date(n)
    r = from_translit(t)

    pass

if __name__ == '__main__':
    test()