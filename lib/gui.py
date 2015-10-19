# -*- coding: utf-8 -*-

"""
GUI module
"""
import os
import re
from PyQt5.QtWidgets import QMainWindow, QWidget, QListWidgetItem, QDialog, QShortcut
from PyQt5.uic import loadUi
from lib.utils import pretty_date

__all__ = ['MainWindow', 'FeedWidgetItem', 'EntryWidgetItem', 'FeedDialog']


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        loadUi('lib/ui/mainwindow.ui', self)

        self.rightWidget.setHidden(True)
        self.leftWidget.setHidden(False)

        self.feedEditBtn.setEnabled(False)
        self.feedDeleteBtn.setEnabled(False)
        self.statusbar.setHidden(True)
        
        self.setWindowTitle('Boogi')

class FeedWidgetItem(QWidget):
    def __init__(self, title, count=None, link=None):
        super(QWidget, self).__init__()
        loadUi('lib/ui/feedwidget.ui', self)

        self.titleLabel.setText(title)
        if link:
            self.linkLabel.setText(link)
        else:
            self.linkLabel.setHidden(True)
        if count:
            self.countLabel.setText(count)
        else:
            self.countLabel.setHidden(True)

class EntryWidgetItem(QWidget):
    def __init__(self, title, date=None, feed=None):
        super(QWidget, self).__init__()
        loadUi('lib/ui/feedwidget.ui', self)

        self.titleLabel.setText(title)
        if feed:
            feed = re.sub(r"#\S+", "", feed).strip()
            self.linkLabel.setText(feed)
        else:
            self.linkLabel.setHidden(True)
        
        if date:
            self.countLabel.setText(pretty_date(date))
        else:
            self.countLabel.setHidden(True)

class FeedDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(QWidget, self).__init__(*args, **kwargs)
        loadUi('lib/ui/feeddialog.ui', self)

    @staticmethod
    def getInputs(parent = None, title=None, link=None):
        dialog = FeedDialog(parent)
        if title:
            dialog.titleEdit.setText(title)
        if link:
            dialog.linkEdit.setText(link)
        result = dialog.exec_()
        title= dialog.titleEdit.text()
        link= dialog.linkEdit.text()
        return (title, link, result == QDialog.Accepted)
