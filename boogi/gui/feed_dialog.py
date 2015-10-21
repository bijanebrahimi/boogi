# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi


class FeedDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(QDialog, self).__init__(*args, **kwargs)
        loadUi('gui/feed_dialog.ui', self)

    @staticmethod
    def getInputs(parent=None, title='', link=''):
        dialog = FeedDialog(parent)
        
        dialog.titleEdit.setText(title)
        dialog.linkEdit.setText(link)
        
        result = dialog.exec_()
        title = dialog.titleEdit.text()
        link = dialog.linkEdit.text()
        return (title, link, result == QDialog.Accepted)
