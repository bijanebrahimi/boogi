# -*- coding: utf-8 -*-

from unicodedata import bidirectional

def _character_direction(ch):
    ch_bidi = bidirectional(ch)
    if ch_bidi in ['L', 'LRE', 'LRO']:
        return 'LTR'
    if ch_bidi in ['R', 'RLE', 'RLO', 'AL']:
        return 'RTL'
    return None

def _rtl(text, default=False):
    if not text:
        return default
    first_character = text[0]
    if bidirectional(first_character) in ['RLE', 'RLO', 'R', 'AL']:
        return True
    elif bidirectional(first_character) in ['LRE', 'LRO', 'L']:
        return False
    elif len(text)>1:
        return _rtl(text[1:])
    return default
    
def html(title, content):
    direction = 'rtl' if _rtl(title) else 'ltr'

    html_code = """
    <html>
        <head>
        </head>
        <body style="direction: {direction}; font-size: 1.2em; font-family: 'Droid Arabic Naskh';">
            <h1>
                {title}
            </h1>
            {content}
        </body>
    </html>""".format(direction=direction, title=title, content=content)
    return html_code
