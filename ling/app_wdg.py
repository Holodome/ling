import dataclasses
import os
from typing import *
import logging

from PyQt5 import QtWidgets, uic

import ling.ling as ling
import ling.db_model as db
import ling.app as app
import ling.sent_wdg as sent_wdg
import ling.sentence_table as sentence_table
import ling.word_table as word_table


def get_config_filename():
    home_folder = os.path.expanduser("~")
    config_file = os.path.join(home_folder, ".ling")
    return config_file


class AppWidget(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        logging.info("Creating AppWidget")
        super().__init__(parent)

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
        logging.info("Deleting AppWidget")
        self.write_db_name()

    def write_db_name(self):
        db_name = app.AppCtx.get().db.filename
        if db_name:
            config_filename = get_config_filename()
            open(config_filename, "w").write(db_name)
            logging.info("Saved to config db %s", db_name)

    def generate_statistics(self):
        logging.info("Generating statistics")
        sentences = app.get().db.get_all_sentences()
        sentence_count = len(sentences)
        logging.info("Sentence count %d", sentence_count)
        self.sent_count_wl.setText("%d" % sentence_count)
        connections = app.get().db.get_all_connections()
        connection_count = len(connections)
        logging.info("Connection count %d", connection_count)
        self.conn_count_wl.setText("%d" % connection_count)
        colls = app.get().db.get_all_collocations()
        coll_count = len(colls)
        logging.info("Coll count %d", coll_count)
        self.coll_count_wl.setText("%d" % coll_count)
        words = app.get().db.get_all_derivative_forms()
        word_count = len(words)
        logging.info("Word count count %d", word_count)
        self.word_count_wl.setText("%d" % word_count)

    def generate_view(self):
        self.generate_statistics()
        self.db_name_le.setText(app.get().db.filename)

    def init_ui(self):
        self.show_all_sent_btn.clicked.connect(self.show_all_sentences)
        self.find_btn.clicked.connect(self.find)
        self.open_bd_btn.clicked.connect(self.open_bd)
        self.update_btn.clicked.connect(self.generate_view)

    def get_entered_word(self):
        text = self.word_enter_le.text()
        text = text.strip()
        return text

    def show_all_sentences(self):
        sentences = app.get().db.get_all_sentences()
        window = QtWidgets.QMainWindow(self)
        table = sentence_table.SentenceTableWidget(sentences)
        window.setCentralWidget(table)
        window.resize(table.size())
        window.show()

    def find(self):
        entered = self.get_entered_word()
        deriv_ids = app.get().db.get_deriv_form_id_by_word(entered)
        words = [app.get().db.get_derivative_form(id_) for id_ in deriv_ids]
        window = QtWidgets.QMainWindow(self)
        table = word_table.WordTableWidget(words)
        window.setCentralWidget(table)
        window.resize(table.size())
        window.show()

    def find_sent(self):
        entered = self.get_entered_word()
        sentences_id = app.get().db.get_sentences_id_by_word(entered)
        sentences = [app.get().db.get_sentence(id_) for id_ in sentences_id]
        window = QtWidgets.QMainWindow(self)
        table = sentence_table.SentenceTableWidget(sentences)
        window.setCentralWidget(table)
        window.resize(table.size())
        window.show()

    def init_for_file(self, filename):
        logging.info("Initializing for db %s", filename)
        app.get().db.create_or_open(filename)
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
