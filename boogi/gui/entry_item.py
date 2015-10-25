# -*- coding: utf-8 -*-

import re
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi
from helpers.date import pretty_date


class EntryItem(QWidget):
    def __init__(self, title, source=None, date=None, read=False):
        super(QWidget, self).__init__()
        loadUi('gui/entry_item.ui', self)
        self.setTitle(title)
        self.setSource(source)
        self.setDate(date)
        self.setRead(read)
        self.setProperty("isRead", '0');

    def setTitle(self, title):
        if len(title)>80:
            self.titleLabel.setText(u"%s …" % title[:80])
        else:
            self.titleLabel.setText(title)
    
    def setDate(self, date=None):
        if date:
            self.dateLabel.setText(pretty_date(date))
            self.dateLabel.setHidden(False)
        else:
            self.dateLabel.setHidden(True)
    
    def setSource(self, source=None):
        if source:
            source = re.sub(r"#\S+", "", source).strip()
            self.sourceLabel.setText("from %s" % source)
            self.sourceLabel.setHidden(False)
        else:
            self.sourceLabel.setHidden(True)
    
    def setRead(self, read):
        # print(dir(self))
        if read:
            self.readLabel.setHidden(False)
            self.readLabel.setText("READ")
        else:
            self.readLabel.setHidden(True)
            
