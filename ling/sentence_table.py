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


class SentenceTableWidget(QtWidgets.QMainWindow):
    COLUMN_NAMES = ["Текст", "Число слов", "Число сочетаний", "Число связей"]
    TEXT_COL = 0x0
    WORD_COUNT_COL = 0x1
    COLL_COUNT_COL = 0x2
    CONN_COUNT_COL = 0x3

    def __init__(self, sentences: List[db.Sentence], *args):
        logging.info("Creating SentenceTableWidget")

        super().__init__(*args)
        self.sentences = sentences

        uic.loadUi("uis/sent_table.ui", self)
        self.init_ui()

        self.display_sentences(sentences)

    def __del__(self):
        logging.info("Deleting SentenceTableWidget")

    def init_ui(self):
        self.edit_btn.clicked.connect(self.ling_edit)
        self.words_btn.clicked.connect(self.find_words)
        self.conn_btn.clicked.connect(self.find_conns)
        self.coll_btn.clicked.connect(self.find_colls)

    def display_sentences(self, sentences):
        self.table.setRowCount(len(sentences))
        self.table.setColumnCount(len(self.COLUMN_NAMES))
        for idx, sent in enumerate(sentences):
            sent_text = sent.contents
            item = QtWidgets.QTableWidgetItem(sent_text)
            self.table.setItem(idx, self.TEXT_COL, item)

            item = QtWidgets.QTableWidgetItem(str(len(sent.words)))
            self.table.setItem(idx, self.WORD_COUNT_COL, item)

            item = QtWidgets.QTableWidgetItem(str(len(sent.collocations)))
            self.table.setItem(idx, self.COLL_COUNT_COL, item)

            item = QtWidgets.QTableWidgetItem(str(len(sent.connections)))
            self.table.setItem(idx, self.CONN_COUNT_COL, item)

        self.table.setHorizontalHeaderLabels(self.COLUMN_NAMES)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def ling_edit(self):
        # @NOTE(hl): This function name because 'edit' is reserved by Qt
        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            sel_id = self.sentences[selected].id

            sent_ctx = app.get().create_sent_ctx_from_db(sel_id)
            widget = sent_wdg.SentenceEditWidget(sent_ctx, self)
            widget.show()

    def find_words(self):
        # @NOTE(hl): To avoid recursion on top level
        from ling.word_table import WordTableWidget

        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            word_ids = self.sentences[selected].words
            words = app.get().get_words_from_ids(word_ids)
            qt_helper.create_widget_window(WordTableWidget(words), self)

    def find_conns(self):
        from ling.connection_table import ConnectionTableWidget

        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            selected_ids = self.sentences[selected].connections
            connections = app.get().get_connections_from_ids(selected_ids)
            qt_helper.create_widget_window(ConnectionTableWidget(connections), self)

    def find_colls(self):
        from ling.collocation_table import CollocationTableWidget

        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            selected_ids = self.sentences[selected].collocations
            collocations = app.get().get_collocations_from_ids(selected_ids)
            qt_helper.create_widget_window(CollocationTableWidget(collocations), self)
