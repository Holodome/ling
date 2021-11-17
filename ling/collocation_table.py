from typing import *
import logging

from PyQt5 import QtWidgets, uic

import ling.ling as ling
import ling.db_model as db
import ling.app as app
import ling.qt_helper as qt_helper


class CollocationTableWidget(QtWidgets.QMainWindow):
    COLUMN_NAMES = ["Тип", "Слова"]
    TYPE_COL = 0x0
    WORDS_COL = 0x1

    def __init__(self, colls: List[db.Collocation], *args):
        logging.info("Creating CollocationTableWidget")

        super().__init__(*args)
        self.colls = colls

        uic.loadUi("uis/coll_table.ui", self)
        self.init_ui()

        self.table.setRowCount(len(colls))
        self.table.setColumnCount(len(self.COLUMN_NAMES))
        for idx, coll in enumerate(colls):
            sem_group = app.get().db.get_semantic_group(coll.semantic_group_id)
            item = QtWidgets.QTableWidgetItem(sem_group.name)
            self.table.setItem(idx, self.TYPE_COL, item)
            words = [app.get().db.get_word(id_) for id_ in coll.words]
            words = ", ".join(map(lambda it: it.word, words))
            item = QtWidgets.QTableWidgetItem(words)
            self.table.setItem(idx, self.WORDS_COL, item)
        self.table.setHorizontalHeaderLabels(self.COLUMN_NAMES)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def __del__(self):
        logging.info("Deleting CollocationTableWidget")

    def find_sent(self):
        from ling.sentence_table import SentenceTableWidget

        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            selected_id = self.colls[selected].id
            # @TODO(hl): SPEED
            sentences = app.get().db.get_all_sentences()
            sentences = list(filter(lambda it: selected_id in it.collocations, sentences))
            qt_helper.create_widget_window(SentenceTableWidget(sentences), self)

    def find_conn(self):
        from ling.connection_table import ConnectionTableWidget

        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            selected_id = self.colls[selected].id
            # @TODO(hl): SPEED
            connections = app.get().db.get_all_connections()
            connections = list(filter(lambda it: selected_id == it.object_ or
                                                 selected_id == it.predicate, connections))
            qt_helper.create_widget_window(ConnectionTableWidget(connections), self)

    def find_words(self):
        from ling.word_table import WordTableWidget

        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            selected_words = self.colls[selected].words
            # @TODO(hl): SPEED
            words = app.get().db.get_all_words()
            words = list(filter(lambda it: it.id in selected_words, words))
            qt_helper.create_widget_window(WordTableWidget(words), self)

    def find_connected(self):
        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            selected_id = self.colls[selected].id
            connected_ids = app.get().db.get_connection_ids_with_coll_id(selected_id)
            print(connected_ids)
            connected = app.get().get_collocations_from_ids(connected_ids)
            qt_helper.create_widget_window(CollocationTableWidget(connected), self)

    def init_ui(self):
        self.conn_btn.clicked.connect(self.find_conn)
        self.sent_btn.clicked.connect(self.find_sent)
        self.words_btn.clicked.connect(self.find_words)
        self.connected_btn.clicked.connect(self.find_connected)


