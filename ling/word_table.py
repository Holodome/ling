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
    COLUMN_NAMES = ["Слово", "Часть речи", "Начальная форма"]
    WORD_COL = 0x0
    POS_COL = 0x1
    INIT_COL = 0x2

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
            item = QtWidgets.QTableWidgetItem(["Нет", "Да"][word.initial_form_id is None])
            self.table.setItem(idx, self.INIT_COL, item)
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

    def find_same_root(self):
        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            selected_word = self.words[selected]
            is_initial = selected_word.initial_form_id is None
            if is_initial:
                word_ids = app.get().db.get_words_with_initial_form(selected_word.id)
                words = app.get().get_words_from_ids(word_ids)
                qt_helper.create_widget_window(WordTableWidget(words), self)
            else:
                init_word = app.get().db.get_word(selected_word.initial_form_id)
                qt_helper.create_widget_window(WordTableWidget([init_word]), self)

    def init_ui(self):
        self.coll_btn.clicked.connect(self.find_coll)
        self.sent_btn.clicked.connect(self.find_sent)
        self.same_root_btn.clicked.connect(self.find_same_root)
