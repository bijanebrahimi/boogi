# -*- coding: utf-8 -*-

import re
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi


class FeedItem(QWidget):
    def __init__(self, title, source=None):
        super(QWidget, self).__init__()
        loadUi('gui/feed_item.ui', self)
        self.setTitle(title)
        self.setSource(source)

    def setTitle(self, title):
        self.titleLabel.setText(title)
    
    def setSource(self, source=None):
        if source:
            match = re.match("^[a-zA-Z]*:?//([^\/]+)(.*)", source)
            if match:
                host, _ = match.groups()
            else:
                host = source
            self.sourceLabel.setText(host)
            self.sourceLabel.setHidden(False)
        else:
            self.sourceLabel.setHidden(True)
    
