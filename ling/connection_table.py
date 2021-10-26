from typing import *
import logging

from PyQt5 import QtWidgets, uic

import ling.ling as ling
import ling.db_model as db
import ling.app as app
import ling.sent_wdg as sent_wdg


class ConnectionTableWidget(QtWidgets.QMainWindow):
    COLUMN_NAMES = ["Предикат", "Октант"]
    PRED_COL = 0x0
    OCT_COL = 0x1

    def __init__(self, conns: List[db.Connection], *args):
        logging.info("Creating ConnectionTableWidget")

        super().__init__(*args)
        self.conns = conns

        uic.loadUi("uis/conn_table.ui", self)
        self.init_ui()

        self.table.setRowCount(len(conns))
        self.table.setColumnCount(len(self.COLUMN_NAMES))
        for idx, word in enumerate(conns):
            print(conns)
            item = QtWidgets.QTableWidgetItem(str(word.predicate))
            self.table.setItem(idx, self.PRED_COL, item)
            item = QtWidgets.QTableWidgetItem(str(word.object_))
            self.table.setItem(idx, self.OCT_COL, item)
        self.table.setHorizontalHeaderLabels(self.COLUMN_NAMES)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def __del__(self):
        logging.info("Deleting ConnectionTableWidget")

    def get_list_of_selected_col_table_rows(self):
        selected_items = self.table.selectedItems()
        rows = set()
        for item in selected_items:
            item_row = item.row()
            rows.add(item_row)
        return list(rows)

    def find_sent(self):
        from ling.sentence_table import SentenceTableWidget

        selected = self.get_list_of_selected_col_table_rows()
        if selected:
            selected = selected[0]
            selected_id = self.conns[selected].id
            # @TODO(hl): SPEED
            sentences = app.get().db.get_all_sentences()
            sentences = list(filter(lambda it: selected_id in it.connections, sentences))

            window = QtWidgets.QMainWindow(self)
            table = SentenceTableWidget(sentences)
            window.setCentralWidget(table)
            window.resize(table.size())
            window.show()

    def find_coll(self):
        from ling.collocation_table import CollocationTableWidget

        selected = self.get_list_of_selected_col_table_rows()
        if selected:
            selected = selected[0]
            selected_ids = [self.conns[selected].object_, self.conns[selected].predicate]
            # @TODO(hl): SPEED
            collocations = app.get().db.get_all_collocations()
            collocations = list(filter(lambda it: it.id in selected_ids, collocations))

            window = QtWidgets.QMainWindow(self)
            table = CollocationTableWidget(collocations)
            window.setCentralWidget(table)
            window.resize(table.size())
            window.show()

    def init_ui(self):
        self.coll_btn.clicked.connect(self.find_coll)
        self.sent_btn.clicked.connect(self.find_sent)


