# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QMainWindow, QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.uic import loadUi


class MainWindow(QMainWindow):
    def __init__(self, title='Boogi', *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        loadUi('gui/main_window.ui', self)
        QShortcut(QKeySequence("Esc"), self, self.toggleArticleView)
        
        self.hideArticleView()
        self.setWindowTitle(title)
    
    def hideArticleView(self):
        self.listView.setHidden(False)
        self.articleView.setHidden(True)
    
    def showArticleView(self):
        self.listView.setHidden(True)
        self.articleView.setHidden(False)
    
    def toggleArticleView(self):
        if self.articleView.isHidden():
            # FIXME: show boogi about in webview
            self.showArticleView()
        else:
            self.hideArticleView()
    
    def setFeedLabel(self, label=None):
        if not label:
            rows_count = self.feedList.count() - 2
            if not rows_count:
                label = 'No feed found'
            else:
                label = '%s feed%s found' % (rows_count, 's' if rows_count-1 else '')
        self.feedLabel.setText(label)
