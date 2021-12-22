import PyQt5.Qt
from PyQt5 import QtWidgets, uic

import functools
import logging

import ling.sentence
import ling.text
import ling.qt_helper
from ling.session import Session
from ling.widgets.change_sg_col import ChangeSGColDialog
from ling.widgets.delete_words_col import DeleteWordsColDialog
from ling.widgets.analysis import AnalysisWidget
from ling.widgets.navigation import NavigationWidget

MODE_ANALYSIS = 0x1
MODE_NAVIGATION = 0x2


class Window(QtWidgets.QMainWindow):
    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session

        uic.loadUi("uis/window.ui", self)
        self.init_ui()

    def init_ui(self):
        self.load_db_btn.clicked.connect(lambda: self.load_db())

        self.stacked = QtWidgets.QStackedWidget(self)
        self.stacked.addWidget(AnalysisWidget(self.session, self))
        self.stacked.addWidget(NavigationWidget(self.session, self))
        self.mode = MODE_NAVIGATION
        self.change_mode()
        self.change_mode_btn.clicked.connect(self.change_mode)

        self.workspace.addWidget(self.stacked)
        if self.session.connected:
            self.init_for_db()

    def init_for_db(self):
        self.db_filename_le.setText(self.session.db.filename)
        self.stacked.currentWidget().on_db_connection()

    def load_db(self):
        if self.session.connected:
            raise NotImplementedError

        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Open db", filter="*.sqlite")[0]
        if filename:
            self.session.init_for_db(filename)
            self.init_for_db()

    def change_mode(self):
        if self.mode == MODE_ANALYSIS:
            self.mode = MODE_NAVIGATION
            self.change_mode_btn.setText("Перейти к навигации")
            self.stacked.setCurrentIndex(1)
        else:
            self.mode = MODE_ANALYSIS
            self.change_mode_btn.setText("Перейти к анализу")
            self.stacked.setCurrentIndex(0)

        if self.session.connected:
            self.stacked.currentWidget().on_db_connection()
        else:
            self.stacked.currentWidget().on_db_connection_loss()
