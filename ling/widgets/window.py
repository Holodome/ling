from PyQt5 import QtWidgets, uic
import logging
from ling.session import Session
from ling.widgets.analysis import AnalysisWidget
from ling.widgets.navigation import NavigationWidget
from uis_generated.window import Ui_MainWindow

MODE_ANALYSIS = 0x1
MODE_NAVIGATION = 0x2


class Window(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.session = session
        self.mode: int

        # uic.loadUi("uis/window.ui", self)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Ling")
        self.load_db_btn.clicked.connect(lambda: self.load_db())
        self.create_db_btn.clicked.connect(lambda: self.create_db())

        self.stacked = QtWidgets.QStackedWidget(self)
        analysis = AnalysisWidget(self.session, self)
        self.stacked.addWidget(analysis)
        self.stacked.addWidget(NavigationWidget(self.session, lambda x: self.change_mode() or analysis.make_sent_edit_cb(x), self))
        self.mode = MODE_NAVIGATION
        self.change_mode()
        self.change_mode_btn.clicked.connect(self.change_mode)

        self.workspace.addWidget(self.stacked)
        if self.session.connected:
            self.init_for_db()

    def init_for_db(self):
        logging.info("Initializing window for db %s" % self.session.db.filename)
        self.db_filename_le.setText(self.session.db.filename)
        self.stacked.currentWidget().on_db_connection()

    def load_db(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Открыть базу данеых", filter="*.sqlite")[0]
        if filename:
            if self.session.connected:
                self.stacked.currentWidget().on_db_connection_loss()

            self.session.init_for_db(filename)
            self.init_for_db()

    def create_db(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Создать базу данных", filter="*.sqlite")[0]
        if filename:
            if self.session.connected:
                self.stacked.currentWidget().on_db_connection_loss()

            self.session.init_for_db(filename)
            self.init_for_db()

    def change_mode(self):
        if self.mode == MODE_ANALYSIS:
            self.mode = MODE_NAVIGATION
            self.change_mode_btn.setText("Перейти к анализу")
            self.stacked.setCurrentIndex(1)
        else:
            self.mode = MODE_ANALYSIS
            self.change_mode_btn.setText("Перейти к навигации")
            self.stacked.setCurrentIndex(0)

        if self.session.connected:
            self.stacked.currentWidget().on_db_connection()
        else:
            self.stacked.currentWidget().on_db_connection_loss()
