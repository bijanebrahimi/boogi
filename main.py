#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QListWidgetItem, QLineEdit, QShortcut
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QVariant

from lib.gui import MainWindow, FeedWidgetItem, EntryWidgetItem, FeedDialog
from lib.utils import feed_parser, is_rtl
from threading import Thread
from queue import Queue
import time
from random import randint


threads_queue = Queue()

# Set new row_factory
def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
    
def update_feed(feed, *args):
    con = sqlite3.connect('db', detect_types=sqlite3.PARSE_DECLTYPES)
    con.row_factory = dict_factory
    
    threads_queue.put('retrieving %s' % feed['link'])
    try:
        xml = feed_parser(feed['link'])
    except Exception as e:
        print('Error', e)
    else:
        threads_queue.put('fetched %s' % feed['link'])
        if not feed:
            threads_queue.put('failed to parse %s' % feed['link'])
        else:
            cur = con.execute("select timestamp from entries where feed_id=? \
                               order by timestamp DESC limit 0,1", (feed['id'], ))
            latest_entry = cur.fetchone()
            if xml and isinstance(xml['entries'], list):
                for entry in xml['entries']:
                    if latest_entry and not latest_entry['timestamp'] < entry['published']:
                        continue
                    
                    con.execute("insert into entries (feed_id, title, link, summary, content, read, timestamp) values(?, ?, ?, ?, ?, ?, ?)",
                        (feed['id'], entry['title'], entry['link'], entry['summary'], None, False, entry['published']))
                con.commit()
            threads_queue.put('updated %s' % feed['link'])
    

class BoogiWindow(MainWindow):
    def __init__(self, *args):
        super(BoogiWindow, self).__init__(*args)
        
        self.page = 1
        self.per_page = 15

        self.feedEdit.textChanged.connect(self.reloadFeedItems)
        self.feedList.itemClicked.connect(self.feedWidgetItemSelected)
        self.feedAddBtn.clicked.connect(self.InsertFeedRow)
        self.feedDeleteBtn.clicked.connect(self.DeleteSelectedFeedRow)
        self.feedEditBtn.clicked.connect(self.UpdateSelectedFeedRow)
        self.feedList.itemDoubleClicked.connect(self.UpdateSelectedFeedRow)
        self.updateAllBtn.clicked.connect(self.UpdateAllFeeds)
        
        self.entryEditWidget.textChanged.connect(self.reloadFeedEntriesItems)
        self.entryListWidget.verticalScrollBar().valueChanged.connect(self.entryListWidgetScrolled)
        self.entryListWidget.itemClicked.connect(self.entryListWidgetItemSelected)
        QShortcut(QKeySequence("Esc"), self, self.keyEscPressed)
        
        self.reloadFeedItems()
    
    
    def entryListWidgetItemSelected(self, item):
        self.rightWidget.setHidden(False)
        self.leftWidget.setHidden(True)
        
        entry = item.row
        title = entry['title']
        if entry['content']:
            content = entry['content'] 
        else:
            content = entry['summary']
        
        rtl = is_rtl(title)
        html = "<html><head><style></style></head><body style=\"text-align: justify; direction: %s; font-size: 1.5em; font-family: 'Droid Arabic Naskh';\"><h1>%s</h1>%s</body></html>" % ('rtl' if rtl else 'ltr', title, content)
        self.webView.setHtml(html)
        
        con.execute("update entries set read = 1 where id = ?", (entry['id'],))
        con.commit()
        
    
    def keyEscPressed(self):
        self.rightWidget.setHidden(True)
        self.leftWidget.setHidden(False)
        
        if self.feedList.currentRow() == 0:
            self.entryListWidget.takeItem(self.entryListWidget.currentRow())
    
    def entryListWidgetScrolled(self, value):
        maximum_value = self.entryListWidget.verticalScrollBar().maximum()
        if value == maximum_value:
            self.reloadFeedEntriesItems(page=self.page+1)

    
    def UpdateAllFeeds(self):
        self.updateAllBtn.setEnabled(False)
        self.feedProgressBar.setValue(0)
        
        #threads = []
        progress_bar_thread = Thread(target=self.updateProgressBar, args=())
        progress_bar_thread.start()

        # Get keyword
        keyword = self.feedEdit.text()
        
        # Select all feeds
        cur = con.execute("SELECT * FROM feeds where title like '%%%s%%' order by id ASC" % keyword)
        
        for feed in cur:
            thread = Thread(target=update_feed, args=(feed, con))
            thread.start()

    def updateProgressBar(self):
        messages_recieved = 0
        total_messages = (self.feedList.count() - 2) * 3
        message = threads_queue.get()
        
        if not total_messages:
            return
        
        while message:
            messages_recieved += 1
            
            self.feedProgressBar.setValue(int((messages_recieved/total_messages)*100))
            
            if messages_recieved >= total_messages:
                break
            
            message = threads_queue.get()
        
        self.updateAllBtn.setEnabled(True)

    def UpdateSelectedFeedRow(self):
        """
        Updates The feed row in database and Updates it's item in feedList
        """
        
        # feed is selected
        list_widget_items = self.feedList.selectedItems()
        if not list_widget_items:
            return
        list_widget_item = list_widget_items[0]
        
        if not hasattr(list_widget_item, 'row'):
            return
        feed = list_widget_item.row
        
        title, link, accepted = FeedDialog.getInputs(title=feed['title'], link=feed['link'])
        if not accepted:
            return
        feed['title'] = title
        feed['link'] = link
        list_widget_item.row = feed

        query = con.execute("update feeds set link = ?, title = ? where id = ?", (link, title, feed['id']))
        con.commit()
        
        feed_widget_item = FeedWidgetItem(title=title, link=link)
        self.feedList.setItemWidget(list_widget_item, feed_widget_item)

    def InsertFeedRow(self):
        """
        Inserts new feed row into database and append it's item to feedList
        """
        title, link, accepted = FeedDialog.getInputs()
        if accepted:
            cur = con.execute("insert into feeds (title, link) values (?, ?)", (title, link))
            id = cur.lastrowid
            con.commit()
            
            self.insertFeedItem(feed=dict(id=id, title=title, link=link))

    def DeleteSelectedFeedRow(self):
        """
        Deletes The feed row from database and remove it's item from feedList
        """
        
        # feed is selected
        selected_feed_items = self.feedList.selectedItems()
        if not selected_feed_items:
            return
        current_feed_item = selected_feed_items[0]
        
        feed = current_feed_item.row
        cur = con.execute("delete from feeds where id = %s" % feed['id'])
        con.commit()
        
        self.feedList.takeItem(self.feedList.currentRow())

    def feedWidgetItemSelected(self, item):
        """
        Check whether a feed is selected
        """
        if item.row:
            self.feedEditBtn.setEnabled(True)
            self.feedDeleteBtn.setEnabled(True)
        else:
            self.feedEditBtn.setEnabled(False)
            self.feedDeleteBtn.setEnabled(False)
        
        self.reloadFeedEntriesItems()
        
    
    def reloadFeedEntriesItems(self, keyword=None, page=None):
        """
        Fills the entryListWidget from database
        """
        # Get keyword
        if not keyword:
            keyword = self.entryEditWidget.text()
        
        # clear entryEditWidget
        if not page:
            self.entryListWidget.clear()
            page = 1
        
        current_feed_item_row = self.feedList.currentRow()
        
        # FIXME
        feed_ids = []
        for index in range(0, self.feedList.count()):
            feed_item_widget = self.feedList.item(index)
            if hasattr(feed_item_widget, 'row'):
                
                feed = feed_item_widget.row 
                if feed:
                    feed_ids.append(feed['id'])
                pass
        
        if current_feed_item_row == 0:
            # Unreads
            args = feed_ids + ['%%%s%%' % keyword]
            args += [(page-1)*self.per_page, self.per_page]
            cur = con.execute("SELECT entries.id, entries.title,\
                feeds.id as feed_id, entries.summary, entries.content,\
                entries.read, entries.`timestamp`, feeds.title as feed_title\
                from entries left join feeds on feeds.id=entries.feed_id\
                where read = 0 and feed_id in (%s) and entries.title like ?\
                order by entries.timestamp DESC\
                limit ?,?" % ','.join('?'*len(feed_ids)), args)
        elif current_feed_item_row == 1:
            args = feed_ids + ['%%%s%%' % keyword]
            args += [(page-1)*self.per_page, self.per_page]
            cur = con.execute("SELECT entries.id, entries.title,\
                feeds.id as feed_id, entries.summary, entries.content,\
                entries.read, entries.`timestamp`, feeds.title as feed_title\
                from entries left join feeds on feeds.id=entries.feed_id\
                where feed_id in (%s) and entries.title like ?\
                order by entries.timestamp DESC\
                limit ?,?" % ','.join('?'*len(feed_ids)), args)
        else:
            # Get current feed item
            selected_feed_items = self.feedList.selectedItems()
            if not selected_feed_items:
                return
            current_feed_item = selected_feed_items[0]
            current_feed_id = current_feed_item.row['id']
            
            args = [current_feed_id, '%%%s%%' % keyword]
            args += [(page-1)*self.per_page, self.per_page]
            cur = con.execute("SELECT entries.id, entries.title,\
                feeds.id as feed_id, entries.summary, entries.content,\
                entries.read, entries.`timestamp`, feeds.title as feed_title\
                from entries left join feeds on feeds.id=entries.feed_id\
                where feed_id == ? and entries.title like ?\
                order by entries.timestamp DESC\
                limit ?,?", args)
        
        if cur:
            self.page = page
            for entry in cur:
                self.insertEntryItem(entry)
        
    def insertEntryItem(self, entry):
        """
        Inserts individual feed items
        """
        entry_widget_item = EntryWidgetItem(title=entry['title'], date=entry['timestamp'], feed=entry['feed_title'])
        list_widget_item = QListWidgetItem()

        list_widget_item.row = entry

        self.entryListWidget.addItem(list_widget_item)
        self.entryListWidget.setItemWidget(list_widget_item, entry_widget_item)
        list_widget_item.setSizeHint(entry_widget_item.sizeHint())
    
    def reloadFeedItems(self, keyword=None):
        """
        Fills the feedList from database
        """
        # Get keyword
        if not keyword:
            keyword = self.feedEdit.text()
        
        # clear feedList listWidget
        self.feedList.clear()

        # Insert [default] Unreads/All items
        self.insertFeedItem(title='Unreads')
        self.insertFeedItem(title='All')

        # Select all feeds
        cur = con.execute("SELECT * FROM feeds where title like '%%%s%%' order by id ASC" % keyword)
        
        affected_rows = 0
        for feed in cur:
            affected_rows += 1
            self.insertFeedItem(feed=feed)

        if affected_rows:
            if not keyword:
                self.feedLabel.setText("Total %s feed%s" % (affected_rows, 's' if affected_rows>1 else ''))
            else:
                self.feedLabel.setText("%s feed%s found" % (affected_rows, 's' if affected_rows>1 else ''))
            self.updateAllBtn.setEnabled(True)
        else:
            self.feedLabel.setText("No feed found")
            self.updateAllBtn.setEnabled(False)

        self.feedEditBtn.setEnabled(False)
        self.feedDeleteBtn.setEnabled(False)

    def insertFeedItem(self, *, title=None, feed=None):
        """
        Inserts individual feed items
        """
        if feed:
            title = feed['title']
            link = feed['link']
        else:
            link = None
        
        feed_widget_item = FeedWidgetItem(title=title, link=link)
        list_widget_item = QListWidgetItem()

        list_widget_item.row = feed

        self.feedList.addItem(list_widget_item)
        self.feedList.setItemWidget(list_widget_item, feed_widget_item)
        list_widget_item.setSizeHint(feed_widget_item.sizeHint())


# CHECK SQLITE DB
path = os.path.expanduser("~/.config/boogi")
db_path = os.path.join(path, 'database.sqlite3')
if not os.path.exists(path):
    os.makedirs(path)
    open(db_path, 'a').close()

con = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
con.row_factory = dict_factory
con.execute('create table if not exists feeds (id integer PRIMARY KEY AUTOINCREMENT, title varchar, link varchar, [timestamp] timestamp);')
con.execute('create table if not exists entries (id integer PRIMARY KEY AUTOINCREMENT, feed_id int, title varchar, summary varchar, content varchar, read bit default 0, link varchar, [timestamp] timestamp, FOREIGN KEY(feed_id) REFERENCES feeds(id));')

def main():
    app = QApplication(sys.argv)
    
    # Show Window
    window = BoogiWindow()
    # window.reloadFeedItems()

    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

