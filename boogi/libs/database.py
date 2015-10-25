# -*- coding: utf-8 -*-

import os
from sqlite3 import connect, PARSE_DECLTYPES

def _dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def _db_path():
    path = os.path.expanduser("~/.config/boogi")
    if not os.path.exists(path):
        os.makedirs(path)
    db_path = os.path.join(path, 'database.sqlite3')
    if not os.path.exists(db_path):
        open(db_path, 'a').close()
    return db_path

def _db_connect():
    connection = connect(_db_path(),
                         detect_types=PARSE_DECLTYPES)
    connection.row_factory = _dict_factory
    return connection

def _check_tables(connection):
    connection.execute('create table if not exists feeds (id integer PRIMARY KEY AUTOINCREMENT, title varchar, link varchar, [timestamp] timestamp);')
    connection.execute('create table if not exists entries (id integer PRIMARY KEY AUTOINCREMENT, feed_id int, title varchar, summary varchar, content varchar, read bit default 0, link varchar, [timestamp] timestamp, FOREIGN KEY(feed_id) REFERENCES feeds(id));')
    connection.commit()

def db_connect():
    connection = _db_connect()
    _check_tables(connection)
    return connection

def db_select_feeds(keyword=None, id=None, ids=None, con=None):
    if not con:
        con = db_connect()
    
    args = []
    where = ''
    if keyword:
        where += 'feeds.title like ? and '
        args.append('%{keyword}%'.format(keyword=keyword))
    
    if id:
        where += 'feeds.id = ? and '
        args.append(id)
    
    if ids:
        where += 'feeds.id in (%s) and ' % (','.join('?'*len(ids)))
        args.extend(ids)
    
    cur = con.execute("SELECT * FROM feeds where " + where + " 1=1 order by id ASC",
                      args)
    return cur

def db_select_entries(*, keyword=None, read=None, feed_id=None, feed_ids=None, id=None, page=1, per_page=60, con=None):
    if not con:
        con = db_connect()
    
    args = []
    where = ''
    if keyword:
        where += 'entries.title like ? and '
        args.append('%{keyword}%'.format(keyword=keyword))
    
    if id:
        where += 'entries.id = ? and '
        args.append(id)
    
    if feed_id:
        where += 'entries.feed_id = ? and '
        args.append(feed_id)
    
    if feed_ids:
        where += 'entries.feed_id in (%s) and ' % (','.join('?'*len(feed_ids)))
        args.extend(feed_ids)
    
    if read is True:
        where += 'entries.read = 1 and '
    elif read is False:
        where += 'entries.read = 0 and '
    
    args.extend([(page-1)*per_page, per_page])
    
    cur = con.execute("SELECT entries.id, entries.title, entries.link,"
            "entries.read, entries.`timestamp`, entries.feed_id, "
            "entries.summary, entries.content, feeds.title as feed_title "
            "from entries left join feeds on feeds.id=entries.feed_id "
            "where " + where + " 1=1 "
            "order by entries.timestamp DESC "
            "limit ?, ?",
            args)
    return cur

def db_select_latest_entry(*, feed_id=None, con=None):
    if not con:
        con = db_connect()
    cur = con.execute("SELECT * from entries WHERE feed_id = ? order by timestamp DESC limit 0,1",
                      (feed_id,))
    try:
        return cur.fetchone()
    except:
        return None

def db_update_feed(*, id, set_title=None, set_link=None, con=None):
    if not con:
        con = db_connect()
    
    args = []
    where_statement = ''
    set_statement = ''
    
    if set_title:
        set_statement += 'title = ?'
        args.append(set_title)
    
    if set_link:
        if set_statement:
            set_statement += ', '
        set_statement += 'link = ?'
        args.append(set_link)
    
    args.append(id)
    cur = con.execute("UPDATE feeds SET " + set_statement +\
            "where id = ?",
            args)
    con.commit()
    return cur

def db_insert_feed(*, title=None, link=None, con=None):
    if not con:
        con = db_connect()
    
    cur = con.execute("INSERT INTO feeds (title, link) VALUES (?, ?)",
                      (title, link))
    con.commit()
    return cur.lastrowid

def db_delete_feed(*, id, con=None):
    if not con:
        con = db_connect()
    
    cur = con.execute("DELETE FROM feeds WHERE id = ?", (id, ))
    cur = con.execute("DELETE FROM entries WHERE feed_id = ?", (id, ))
    con.commit()
    return True

def db_update_entries(*, set_content=None, set_read=None, keyword=None, feed_id=None, feed_ids=None, id=None, ids=None, con=None):
    if not con:
        con = db_connect()
    
    args = []
    where_statement = ''
    set_statement = ''
    
    if set_content:
        set_statement += 'content = ?'
        args.append(set_content)
    
    if set_read in [True, False]:
        if set_statement:
            set_statement += ', '
        set_statement += 'read = ?'
        args.append(set_read)
    
    if keyword:
        where_statement += 'entries.title like ? and '
        args.append('%{keyword}%'.format(keyword=keyword))
    
    if id:
        where_statement += 'entries.id = ? and '
        args.append(id)
    
    if ids:
        where_statement += 'entries.id in (%s) and ' % (','.join('?'*len(ids)))
        args.extend(ids)
    
    if feed_id:
        where_statement += 'entries.feed_id = ? and '
        args.append(feed_id)
    
    if feed_ids:
        where_statement += 'entries.feed_id in (%s) and ' % (','.join('?'*len(feed_ids)))
        args.extend(feed_ids)
    
    cur = con.execute("UPDATE entries SET " + set_statement +\
            "where " + where_statement + " 1=1 ",
            args)
    con.commit()
    return cur

def db_insert_entry(*, feed_id=None, title=None, link=None, summary='', content='', timestamp=None, con=None):
    if not con:
        con = db_connect()
    cur = con.execute("INSERT INTO entries (feed_id, title, link, summary, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                      (feed_id, title, link, summary, content, timestamp))
    
    con.commit()
    return cur.lastrowid
