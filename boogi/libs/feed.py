# -*- coding: utf-8 -*-

from feedparser import parse
from datetime import datetime
from time import mktime


def _normalize_feed(xml):
    feed = xml.get('feed', {})
        
    return dict(
        link=feed.get('link', ''),
        title=xml.get('title', '')
    )

def _normalize_entries(xml):
    entries = xml.get('entries', [])
    normalized_entries = []
    for entry in entries:
        updated = entry.get('updated_parsed', None)
        if not updated:
            updated = datetime.now()
        else:
            updated = datetime.fromtimestamp(mktime(updated))
        
        published = entry.get('published_parsed', None)
        if not published:
            published = updated
        else:
            published = datetime.fromtimestamp(mktime(published))
        
        content = entry.get('content', None)
        summary = entry.get('summary', content)
        
        normalized_entries.append(dict(
            title=entry.get('title', ''),
            link=entry.get('link', ''),
            author=entry.get('author', ''),
            summary=summary,
            published=published,
            updated=updated
        ))
    return normalized_entries
    

def feed_parser(url):
    """
    Returns normalized feed in a dictionary object. this normalized feed has
    the very basic and common keys as show below:
        title
        link
        entries
            title
            link
            author
            updated
            published
            summary
    """
    xml = parse(url)
    return dict(
        feed=_normalize_feed(xml),
        entries=_normalize_entries(xml)
    )

