# -*- coding: utf-8 -*-

from time import mktime
from datetime import datetime
import requests
# from readability.readability import Document
# from feedparser import parse
import feedparser
import unicodedata



__all__ = ['feed_parser', 'pretty_date', 'is_rtl']

def is_rtl(text):
    ltr_chars = 0
    rtl_chars = 0
    for ch in text:
        ch_code = unicodedata.bidirectional(ch)
        if ch_code in ['L', 'LRO', 'LRE']:
            ltr_chars += 1
        elif ch_code in ['R', 'AL', 'RLO', 'RLE']:
            rtl_chars += 1
        return rtl_chars > ltr_chars

def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time
    else:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(int(second_diff / 60)) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(int(second_diff / 3600)) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(int(day_diff / 7)) + " weeks ago"
    if day_diff < 365:
        return str(int(day_diff / 30)) + " months ago"
    return str(int(day_diff / 365)) + " years ago"

def feed_parser(url, proxies=None):
    """
    Returns feed
    
    Args:
        url: article's url
        proxies: a key/value dictionary protocol:location object
                 You can also configure proxies by setting the environment
                 variables HTTP_PROXY and HTTPS_PROXY.
                 $ export HTTP_PROXY="http://10.10.1.10:3128"
                 $ export HTTPS_PROXY="http://10.10.1.10:1080"
    """
    
    xml = feedparser.parse(url)
    
    if not xml or not xml.get('entries') or not xml.get('feed'):
        return None
    
    if 'updated_parsed' in xml.entries[0].keys():
        date_attr = 'updated_parsed'
    elif 'published_parsed' in xml.entries[0].keys():
        date_attr = 'published_parsed'
    else:
        return None
        
    
    if xml.get('version', '').startswith('atom'):
        feed = dict(title=xml.feed.title,
            link=xml.feed.link,
            entries=[])
        for entry in xml.entries:
            feed['entries'].append(dict(title=entry.title,
                link=entry.link,
                published=datetime.fromtimestamp(mktime(getattr(entry, date_attr))),
                summary=entry.summary))
        return feed
    # elif xml.version.startswith('rss'):
    else:
        feed = dict(title=xml.feed.get('title', ''),
            link=xml.feed.get('link', ''),
            entries=[])
        for entry in xml.entries:
            feed['entries'].append(dict(title=entry.title,
                link=entry.link,
                published=datetime.fromtimestamp(mktime(getattr(entry, date_attr))),
                summary=entry.summary))
        return feed
    #else:
    #    return None
