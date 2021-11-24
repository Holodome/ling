from typing import *
import logging

from PyQt5 import QtWidgets, uic

import ling.ling as ling
import ling.db_model as db
import ling.app as app
import ling.sent_wdg as sent_wdg
import ling.qt_helper as qt_helper


class ConnectionTableWidget(QtWidgets.QMainWindow):
    COLUMN_NAMES = ["Предикат", "Октант", "Семантическая группа"]
    PRED_COL = 0x0
    OCT_COL = 0x1
    SEM_COL = 0x2

    def __init__(self, conns: List[db.Connection], *args):
        logging.info("Creating ConnectionTableWidget")

        super().__init__(*args)
        self.conns = conns

        uic.loadUi("uis/conn_table.ui", self)
        self.init_ui()

        self.table.setRowCount(len(conns))
        self.table.setColumnCount(len(self.COLUMN_NAMES))
        for idx, word in enumerate(conns):
            pred = app.get().db.get_collocation(word.predicate)
            item = QtWidgets.QTableWidgetItem(str(pred.text))
            self.table.setItem(idx, self.PRED_COL, item)

            obj = app.get().db.get_collocation(word.object_)
            item = QtWidgets.QTableWidgetItem(str(obj.text))
            self.table.setItem(idx, self.OCT_COL, item)

            sg = app.get().db.get_semantic_group(obj.semantic_group_id)
            item = QtWidgets.QTableWidgetItem(str(sg.name))
            self.table.setItem(idx, self.SEM_COL, item)
        self.table.setHorizontalHeaderLabels(self.COLUMN_NAMES)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def __del__(self):
        logging.info("Deleting ConnectionTableWidget")

    def find_sent(self):
        from ling.sentence_table import SentenceTableWidget

        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            selected_id = self.conns[selected].id
            # @TODO(hl): SPEED
            sentences = app.get().db.get_all_sentences()
            sentences = list(filter(lambda it: selected_id in it.connections, sentences))
            qt_helper.create_widget_window(SentenceTableWidget(sentences), self)

    def find_coll(self):
        from ling.collocation_table import CollocationTableWidget

        selected = qt_helper.table_get_selected_rows(self.table)
        if selected:
            selected = selected[0]
            selected_ids = [self.conns[selected].object_, self.conns[selected].predicate]
            # @TODO(hl): SPEED
            collocations = app.get().db.get_all_collocations()
            collocations = list(filter(lambda it: it.id in selected_ids, collocations))
            qt_helper.create_widget_window(CollocationTableWidget(collocations), self)

    def init_ui(self):
        self.coll_btn.clicked.connect(self.find_coll)
        self.sent_btn.clicked.connect(self.find_sent)


