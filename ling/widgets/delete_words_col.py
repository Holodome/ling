import PyQt5.Qt
from PyQt5 import QtWidgets, uic

from ling.session import Session
from uis_generated.delete_words_col import Ui_Dialog
from typing import List


class DeleteWordsColDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, session: Session, col_str: str, words_list: List[str], parent=None):
        super().__init__(parent)
        self.session = session
        self.setupUi(self)
        # uic.loadUi("uis/delete_words_col.ui", self)
        self.preview_field.setText(col_str)
        self.word_list.setSelectionMode(PyQt5.Qt.QAbstractItemView.MultiSelection)
        for idx, word in enumerate(words_list):
            self.word_list.insertItem(idx, QtWidgets.QListWidgetItem(word))
