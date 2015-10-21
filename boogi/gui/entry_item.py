# -*- coding: utf-8 -*-

import re
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi
from helpers.date import pretty_date


class EntryItem(QWidget):
    def __init__(self, title, source=None, date=None):
        super(QWidget, self).__init__()
        loadUi('gui/entry_item.ui', self)
        self.setTitle(title)
        self.setSource(source)
        self.setDate(date)

    def setTitle(self, title):
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
    
    def setAsRead(self):
        title = self.titleLabel.text()
        # FIXME: implement the visual look
        # self.titleLabel.setText("[%s]" % title)

