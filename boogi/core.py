# -*- coding: utf-8 -*-

from weakref import ref
from gui.main_window import MainWindow
from gui.feed_item import FeedItem
from gui.entry_item import EntryItem
from libs.database import db_connect, db_select_feeds, db_select_entries, \
                          db_update_entries, db_update_feed, db_insert_feed, \
                          db_delete_feed, db_insert_entry, \
                          db_select_latest_entry
from libs.feed import feed_parser
from gui.feed_dialog import FeedDialog
from helpers.html import html
from PyQt5.QtWidgets import QListWidgetItem
from readability.readability import Document
from threading import Thread
import requests
from queue import Queue


jobs_queue = Queue()

con = db_connect()
feed_idx = {}
entry_idx = {}

UNREAD_ITEMS = 0
ALL_ITEMS = 1
entry_page = 1
entries_per_page = 40

class BoogiWindow(MainWindow):
    def __init__(self, *args):
        super(BoogiWindow, self).__init__(*args)
        
        self.feedEdit.returnPressed.connect(self.reloadFeeds)
        self.reloadFeeds()
        
        self.feedList.itemClicked.connect(self.reloadEntries)
        self.entryEditWidget.returnPressed.connect(self.reloadEntries)
        self.entryListWidget.itemClicked.connect(self.showEntry)
        
        self.feedAddBtn.clicked.connect(self.InsertFeed)
        self.feedDeleteBtn.clicked.connect(self.deleteFeed)
        self.feedEditBtn.clicked.connect(self.updateFeed)
        self.feedList.itemDoubleClicked.connect(self.updateFeed)
        self.updateAllBtn.clicked.connect(self.updateFeeds)
        
        self.entryListWidget.verticalScrollBar().valueChanged.connect(self.loadNextEntries)
        
        self.readabilityBtn.clicked.connect(self.readabilityBtnClicked)
    
    def reloadFeeds(self):
        global feed_idx
        keyword = self.feedEdit.text()
        
        # FIXME: only clear items inserted after Unread/All
        feed_idx = {}
        self.feedList.clear()
        
        # FIXME: add Unreads/All once when initializing window
        self.insertFeedItem(title='Unreads', link='News you haven\'t read yet')
        self.insertFeedItem(title='All', link='See all the items')

        cur = db_select_feeds(keyword=keyword, con=con)
        self.feedEditBtn.setEnabled(False)
        self.feedDeleteBtn.setEnabled(False)
        
        for feed in cur:
            feed_id = feed['id']
            list_item, feed_item = self.insertFeedItem(feed=feed)
            list_item.feed_id = feed_id
            feed_idx[feed_id] = (ref(list_item), ref(feed_item))
        
    def insertFeedItem(self, title=None, link=None, feed=None):
        if not feed:
            feed = {}
        
        title = feed.get('title', title)
        link = feed.get('link', link)
        
        feed_item = FeedItem(title=title, source=link)
        list_item = QListWidgetItem()

        self.feedList.addItem(list_item)
        self.feedList.setItemWidget(list_item, feed_item)
        list_item.setSizeHint(feed_item.sizeHint())
        
        return list_item, feed_item
    
    def reloadEntries(self, item=None, page=1):
        global entry_page, entry_idx
        
        entry_page = page
        keyword = self.entryEditWidget.text()
        
        current_row = self.feedList.currentRow()
        feed_ids = feed_idx.keys()
        
        # FIXME: only clear items inserted after Unread/All
        if page == 1:
            entry_idx = {}
            self.entryListWidget.clear()
        
        if current_row in [UNREAD_ITEMS, ALL_ITEMS]:
            self.feedEditBtn.setEnabled(False)
            self.feedDeleteBtn.setEnabled(False)
        
        if current_row == UNREAD_ITEMS:
            cur = db_select_entries(keyword=keyword,
                                    feed_ids=feed_ids,
                                    read=False,
                                    page=page,
                                    per_page=entries_per_page,
                                    con=con)
        elif current_row == ALL_ITEMS:
            cur = db_select_entries(keyword=keyword,
                                    feed_ids=feed_ids,
                                    page=page,
                                    per_page=entries_per_page,
                                    con=con)
        else:
            # Get current feed item
            if not item:
                item = self.feedList.currentItem()
            
            if not hasattr(item, 'feed_id'):
                return
            
            self.feedEditBtn.setEnabled(True)
            self.feedDeleteBtn.setEnabled(True)
            
            cur = db_select_entries(keyword=keyword,
                                    feed_id=item.feed_id,
                                    page=page,
                                    per_page=20,
                                    con=con)
        for entry in cur:
            self.insertEntry(entry=entry)
            
    
    def insertEntry(self, entry):
        global entry_idx
        
        entry_id = entry['id']
        entry_item = EntryItem(title=entry['title'],
                               date=entry['timestamp'],
                               source=entry['feed_title'])
        list_item = QListWidgetItem()
        
        list_item.entry_id = entry_id
        entry_idx[entry_id] = (ref(list_item), ref(entry_item))

        self.entryListWidget.addItem(list_item)
        self.entryListWidget.setItemWidget(list_item, entry_item)
        list_item.setSizeHint(entry_item.sizeHint())
        
        return (list_item, entry_item)
    
    def showEntry(self, item):
        global entry_idx
        self.showArticleView()
        
        entry_id = item.entry_id
        cur = db_select_entries(id=entry_id)
        entry = cur.fetchone()
        
        title = entry['title']
        link = entry['link']
        self.sourceLabel.setText(link)
        if entry['content']:
            content = entry['content'] 
            self.readabilityBtn.setChecked(True)
        else:
            self.readabilityBtn.setChecked(False)
            content = entry['summary']
        
        self.webView.setHtml(html(title, content))
        # FIXME: set entry_item style to show it has been read
        db_update_entries(id=entry_id, set_read=True)
        entry_idx[entry_id][1]().setAsRead()

    def loadNextEntries(self, value):
        global entry_page
        maximum = self.entryListWidget.verticalScrollBar().maximum()
        if not maximum or (value/maximum)>.9:
            self.reloadEntries(page=entry_page+1)

    def readabilityBtnClicked(self):
        item = self.entryListWidget.currentItem()
        if not item:
            return
        entry_id = item.entry_id
        
        cur = db_select_entries(id=entry_id)
        entry = cur.fetchone()
        entry_link = entry['link']
        entry_title = entry['title']
        entry_content = entry['content']
        entry_summary = entry['summary']
        
        if self.readabilityBtn.isChecked():
            if not entry_content:
                try:
                    response = requests.get(entry_link)
                except Exception as e:
                    pass
                else:
                    entry_content = Document(response.text).summary()
                    if entry_content and entry_content!='<body id="readabilityBody"/>':
                        db_update_entries(id=entry_id, set_content=entry_content)
                    else:
                        entry_content = ''
            if not entry_content:
                self.readabilityBtn.setChecked(False)
                entry_content = entry_summary
        else:
            entry_content = entry_summary
        self.webView.setHtml(html(entry_title, entry_content))

    def updateFeed(self, item=None):
        global feed_idx
        if not item:
            item = self.feedList.currentItem()
        
        if not hasattr(item, 'feed_id'):
            return
        
        feed_id = item.feed_id
        cur = db_select_feeds(id=feed_id)
        feed = cur.fetchone()
        
        title, link, accepted = FeedDialog.getInputs(title=feed['title'], link=feed['link'])
        if not accepted:
            return
        feed['title'] = title
        feed['link'] = link
        
        db_update_feed(id=feed_id, set_title=title, set_link=link)
        item_list, feed_item = feed_idx[feed_id]
        feed_item().setTitle(title)
        feed_item().setSource(link)

    def InsertFeed(self):
        global feed_idx
        title, link, accepted = FeedDialog.getInputs()
        if not accepted:
            return
        
        feed_id = db_insert_feed(title=title, link=link)
        list_item, feed_item = self.insertFeedItem(title=title, link=link)
        list_item.feed_id = feed_id
        feed_idx[feed_id] = (ref(list_item), ref(feed_item))
    
    def deleteFeed(self):
        global feed_idx
        
        item = self.feedList.currentItem()
        if not hasattr(item, 'feed_id'):
            return
        
        feed_id = item.feed_id
        db_delete_feed(id=feed_id, con=con)
        
        self.feedList.takeItem(self.feedList.currentRow())
        del feed_idx[feed_id]

    def fetchEntries(self, feed_link, feed_id, latest=None):
        global jobs_queue
        feed_dict = feed_parser(feed_link)
        try:
            pass
        except Exception as e:
            # FIXME: use logger
            print('DEBUG', e)
        else:
            for entry in feed_dict['entries']:
                if not latest or latest < entry['published']:
                    db_insert_entry(title=entry['title'],
                            link=entry['link'],
                            summary=entry['summary'],
                            content='',
                            timestamp=entry['published'],
                            feed_id=feed_id)
        finally:
            jobs_queue.put(feed_link)
    
    def updateFeeds(self):
        global feed_idx
        feed_ids = feed_idx.keys()
        self.feedProgressBar.setValue(0)
        self.updateAllBtn.setEnabled(False)
        total = len(feed_ids)
        cur = db_select_feeds(ids=feed_ids, con=con)
        
        thread = Thread(target=self.updateProgressBar, args=())
        thread.start()
        
        for feed in cur:
            feed_id = feed['id']
            feed_link = feed['link']
            latest_entry = db_select_latest_entry(feed_id=feed_id)
            # FIXME: need cleaning up
            if not latest_entry:
                latest_entry = {}
            thread = Thread(target=self.fetchEntries, args=(feed_link, feed_id, latest_entry.get('timestamp')))
            thread.start()
            

    def updateProgressBar(self):
        global feed_idx

        jobs_total = len(feed_idx)
        jobs_done = 0
        
        if not jobs_total:
            return
        
        message = jobs_queue.get()
        while message:
            jobs_done += 1
            
            progress = int((jobs_done/jobs_total)*100)
            self.feedProgressBar.setValue(progress)
            if jobs_done == jobs_total:
                break
            message = jobs_queue.get()
        
        self.updateAllBtn.setEnabled(True)
        self.feedProgressBar.setValue(0)

