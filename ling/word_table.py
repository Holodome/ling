import dataclasses
import os
from typing import *
import logging

from PyQt5 import QtWidgets, uic

import ling.ling as ling
import ling.db_model as db
import ling.app as app
import ling.sent_wdg as sent_wdg
import ling.qt_helper as qt_helper


class WordTableWidget(QtWidgets.QMainWindow):
    COLUMN_NAMES = ["Слово", "Часть речи"]
    WORD_COL = 0x0
    POS_COL = 0x1

    def __init__(self, words: List[db.Word], *args):
        logging.info("Creating WordTableWidget")

        super().__init__(*args)
        self.words = words

        uic.loadUi("uis/word_table.ui", self)
        self.init_ui()

        self.table.setRowCount(len(words))
        self.table.setColumnCount(len(self.COLUMN_NAMES))
        for idx, word in enumerate(words):
            item = QtWidgets.QTableWidgetItem(word.word)
            self.table.setItem(idx, self.WORD_COL, item)
            item = QtWidgets.QTableWidgetItem(str(word.part_of_speech))
            self.table.setItem(idx, self.POS_COL, item)
        self.table.setHorizontalHeaderLabels(self.COLUMN_NAMES)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def __del__(self):
        logging.info("Deleting WordTableWidget")

    def find_sent(self):
        from ling.sentence_table import SentenceTableWidget

        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            selected_id = self.words[selected].id
            # @TODO(hl): SPEED
            sentences = app.get().db.get_all_sentences()
            sentences = list(filter(lambda it: selected_id in it.words, sentences))
            qt_helper.create_widget_window(SentenceTableWidget(sentences), self)

    def find_coll(self):
        from ling.collocation_table import CollocationTableWidget

        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            selected_id = self.words[selected].id
            # @TODO(hl): SPEED
            collocations = app.get().db.get_all_collocations()
            collocations = list(filter(lambda it: selected_id in it.words, collocations))
            qt_helper.create_widget_window(CollocationTableWidget(collocations), self)

    def init_ui(self):
        self.coll_btn.clicked.connect(self.find_coll)
        self.sent_btn.clicked.connect(self.find_sent)


