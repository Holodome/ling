import PyQt5.Qt
from PyQt5 import QtWidgets, uic

from ling.session import Session


class DeleteWordsColDialog(QtWidgets.QDialog):
    def __init__(self, session: Session, col_str: str, words_list: list[str], parent=None):
        super().__init__(parent)
        self.session = session
        uic.loadUi("uis/delete_words_col.ui", self)
        self.preview_field.setText(col_str)
        self.word_list.setSelectionMode(PyQt5.Qt.QAbstractItemView.MultiSelection)
        for idx, word in enumerate(words_list):
            self.word_list.insertItem(idx, QtWidgets.QListWidgetItem(word))
