import logging
import os

from PyQt5 import QtWidgets, uic
from .ling import *
from .db_model import DBCtx


def get_config_filename():
    home_folder = os.path.expanduser("~")
    config_file = os.path.join(home_folder, ".ling")
    return config_file


class SentenceTableWidget(QtWidgets.QTableWidget):
    def __init__(self, ctx, sentence_ids: List[int], *args):
        super().__init__(*args)


class AppWidget(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DBCtx()

        uic.loadUi("uis/app.ui", self)
        self.init_ui()

        config_file = get_config_filename()
        logging.debug("Config filepath %s", config_file)
        if os.path.exists(config_file):
            file_contents = open(config_file).read()
            logging.debug("Config contents %s", file_contents)
            db_name = file_contents
            if os.path.exists(db_name):
                logging.info("Found record of open database %s in config", db_name)
                self.init_for_file(db_name)
            else:
                os.remove(config_file)

    def __del__(self):
        self.write_db_name()

    def write_db_name(self):
        db_name = self.db.filename
        if db_name:
            config_filename = get_config_filename()
            open(config_filename, "w").write(db_name)
            logging.info("Saved to config db %s", db_name)

    def generate_statistics(self):
        sentences = self.db.get_all_sentences()
        sentence_count = len(sentences)
        self.sent_count_wl.setText("%d" % sentence_count)
        connections = self.db.get_all_connections()
        connection_count = len(connections)
        self.conn_count_wl.setText("%d" % connection_count)
        colls = self.db.get_all_collocations()
        coll_count = len(colls)
        self.coll_count_wl.setText("%d" % coll_count)
        words = self.db.get_all_derivative_forms()
        word_count = len(words)
        self.word_count_wl.setText("%d" % word_count)

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

    def get_entered_word(self):
        text = self.word_enter_le.text()
        text = text.strip()
        return text

    def show_all_sentences(self):
        sentence_ids = self.db.get_sentence_id()
        for sid in sentence_ids:
            text = self.db.get_sentence_text(sid)
            print(text)

    def find_coll(self):
        ...

    def find_conn(self):
        ...

    def find_init(self):
        ...

    def find_sent(self):
        ...

    def init_for_file(self, filename):
        logging.info("Initializing for db %s", filename)
        self.db.create_or_open(filename)
        self.generate_view()

    def open_bd(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Open file", filter="*.sqlite")[0]
        if filename:
            self.init_for_file(filename)


def test_app_wdg():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    exec = AppWidget()
    exec.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_app_wdg()
