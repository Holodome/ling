from PyQt5 import QtWidgets, uic
from ling import *
from db_model import DBCtx


class AppWidget(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DBCtx()
        self.ctx = GlobalLingContext()

        uic.loadUi("../uis/app.ui", self)
        self.init_ui()

    def generate_statistics(self):
        ...

    def generate_view(self):
        self.generate_statistics()
        self.db_name_le.setText(self.db.filename)

    def init_ui(self):
        """
        show_all_sent_btn
        find_coll_btn
        find_conn_btn
        find_init_btn
        find_sent_btn
        open_bd_btn

        coll_count_wl
        conn_count_wl
        open_bd_wl
        sent_count_wl
        word_count_wl
        word_enter_le
        """
        self.show_all_sent_btn.clicked.connect(self.show_all_sentences)
        self.find_coll_btn.clicked.connect(self.find_coll)
        self.find_conn_btn.clicked.connect(self.find_conn)
        self.find_init_btn.clicked.connect(self.find_init)
        self.find_sent_btn.clicked.connect(self.find_sent)
        self.open_bd_btn.clicked.connect(self.open_bd)

        self.generate_view()

    def get_entered_word(self):
        text = self.word_enter_le.text()
        text = text.strip()

    def show_all_sentences(self):
        ...

    def find_coll(self):
        ...

    def find_conn(self):
        ...

    def find_init(self):
        ...

    def find_sent(self):
        ...

    def open_bd(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Open file", filter="*.sqlite")[0]
        if filename:
            self.db.create_or_open(filename)
            self.generate_view()


def test_app_wdg():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    exec = AppWidget()
    exec.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_app_wdg()
