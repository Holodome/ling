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


class SemanticGroupsWidget(QtWidgets.QMainWindow):
    COLUMN_NAMES = ["Название", "Число сочетаний", "Число слов"]
    NAME_COL = 0x0
    COLLS_COL = 0x1
    WORDS_COL = 0x2

    def __init__(self, *args):
        logging.info("Creating SemanticGroupsWidget")

        super().__init__(*args)

        uic.loadUi("uis/sem_groups.ui", self)
        self.init_ui()
        
        self.generate_view()
                
    def generate_view(self):
        all_sg = app.get().db.get_all_semantic_groups()
        self.all_sg = all_sg
        
        self.table.setRowCount(len(all_sg))
        self.table.setColumnCount(len(self.COLUMN_NAMES))
        self.table.setHorizontalHeaderLabels(self.COLUMN_NAMES)
        
        for idx, sg in enumerate(all_sg):
            item = QtWidgets.QTableWidgetItem(sg.name)
            self.table.setItem(idx, self.NAME_COL, item)
            
            colls = app.get().db.get_collocations_of_sem_group(sg.id)
            item = QtWidgets.QTableWidgetItem(str(len(colls)))
            self.table.setItem(idx, self.COLLS_COL, item)
            # @TODO(hl): SPEED
            words = app.get().db.get_words_of_sem_group(sg.id)
            item = QtWidgets.QTableWidgetItem(str(len(words)))
            self.table.setItem(idx, self.WORDS_COL, item)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def __del__(self):
        logging.info("Deleting SemanticGroupsWidget")

    def init_ui(self):
        self.add_btn.clicked.connect(self.add_sg)
        self.colls_btn.clicked.connect(self.show_colls)
        self.del_btn.clicked.connect(self.del_sg)
        self.words_btn.clicked.connect(self.show_words)
        
        self.generate_view()

    def add_sg(self):
        name = QtWidgets.QInputDialog.getText(self, "Название", "Название: ")
        if name[1]:
            name = name[0]
            app.get().db.add_semantic_group(name)
            self.generate_view()
            
    def del_sg(self):
        rows = qt_helper.table_get_selected_rows(self.table)
        if rows:
            for row in rows:
                id_ = self.all_sg[row].id
                app.get().db.remove_semantic_group(id_)
            self.generate_view()
            
    def show_colls(self):
        from ling.collocation_table import CollocationTableWidget
        rows = qt_helper.table_get_selected_rows(self.table)
        if rows:
            row = rows[0]
            id_ = self.all_sg[row].id
            coll_ids = app.get().db.get_collocations_of_sem_group(id_)
            colls = [app.get().db.get_collocation(id_) for id_ in coll_ids]

            window = QtWidgets.QMainWindow(self)
            table = CollocationTableWidget(colls)
            window.setCentralWidget(table)
            window.resize(table.size())
            window.show()

    def show_words(self):
        from ling.word_table import WordTableWidget
        rows = qt_helper.table_get_selected_rows(self.table)
        if rows:
            row = rows[0]
            id_ = self.all_sg[row].id
            word_ids = app.get().db.get_words_of_sem_group(id_)
            words = [app.get().db.get_word(id_) for id_ in word_ids]
            
            window = QtWidgets.QMainWindow(self)
            table = WordTableWidget(words)
            window.setCentralWidget(table)
            window.resize(table.size())
            window.show()

    
    