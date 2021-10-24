import dataclasses
import os
from typing import *
import logging

from PyQt5 import QtWidgets, uic

import ling.ling as ling
import ling.db_model as db
import ling.app as app
import ling.sent_wdg as sent_wdg


def get_config_filename():
    home_folder = os.path.expanduser("~")
    config_file = os.path.join(home_folder, ".ling")
    return config_file


class WordTableWidget(QtWidgets.QMainWindow):
    COLUMN_NAMES = ["Слово", "Часть речи"]
    WORD_COL = 0x0
    POS_COL = 0x1

    def __init__(self, words: List[db.DerivativeForm], *args):
        logging.info("Creating WordTableWidget")

        super().__init__(*args)
        self.words = words

        uic.loadUi("uis/word_table.ui", self)
        self.init_ui()

        self.table.setRowCount(len(words))
        self.table.setColumnCount(len(self.COLUMN_NAMES))
        for idx, word in enumerate(words):
            item = QtWidgets.QTableWidgetItem(word.form)
            self.table.setItem(idx, self.WORD_COL, item)
            item = QtWidgets.QTableWidgetItem(str(word.part_of_speech))
            self.table.setItem(idx, self.POS_COL, item)
        self.table.setHorizontalHeaderLabels(self.COLUMN_NAMES)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def __del__(self):
        logging.info("Deleting WordTableWidget")

    def init_ui(self):
        self.coll_btn.clicked.connect(self.find_coll)
        self.sent_btn.clicked.connect(self.find_sent)

    def get_list_of_selected_col_table_rows(self):
        selected_items = self.table.selectedItems()
        rows = set()
        for item in selected_items:
            item_row = item.row()
            rows.add(item_row)
        return list(rows)

    def find_sent(self):
        selected = self.get_list_of_selected_col_table_rows()
        if selected:
            selected = selected[0]
            selected_id = self.words[selected].id
            # @TODO(hl): SPEED
            sentences = app.get().db.get_all_sentences()
            sentences = list(filter(lambda it: selected_id in it.words, sentences))

            window = QtWidgets.QMainWindow(self)
            table = SentenceTableWidget(sentences)
            window.setCentralWidget(table)
            window.resize(table.size())
            window.show()

    def find_coll(self):
        ...


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

            item = QtWidgets.QTableWidgetItem(str(sent.word_count))
            self.table.setItem(idx, self.WORD_COUNT_COL, item)

            item = QtWidgets.QTableWidgetItem(str(len(sent.collocations)))
            self.table.setItem(idx, self.COLL_COUNT_COL, item)

            item = QtWidgets.QTableWidgetItem(str(len(sent.connections)))
            self.table.setItem(idx, self.CONN_COUNT_COL, item)

        self.table.setHorizontalHeaderLabels(self.COLUMN_NAMES)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def get_list_of_selected_col_table_rows(self):
        selected_items = self.table.selectedItems()
        rows = set()
        for item in selected_items:
            item_row = item.row()
            rows.add(item_row)
        return list(rows)

    def ling_edit(self):
        # @NOTE(hl): This function name because 'edit' is reserved by Qt
        selected = self.get_list_of_selected_col_table_rows()
        if selected:
            selected = selected[0]
            sel_id = self.sentences[selected].id

            sent_ctx = app.get().create_sent_ctx_from_db(sel_id)
            widget = sent_wdg.SentenceEditWidget(sent_ctx, self)
            widget.show()

    def find_words(self):
        selected = self.get_list_of_selected_col_table_rows()
        if selected:
            selected = selected[0]
            word_ids = self.sentences[selected].words
            words = [app.get().db.get_derivative_form(id_) for id_ in word_ids]
            window = QtWidgets.QMainWindow(self)
            table = WordTableWidget(words)
            window.setCentralWidget(table)
            window.resize(table.size())
            window.show()

    def find_conns(self):
        pass

    def find_colls(self):
        pass


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
        table = SentenceTableWidget(sentences)
        window.setCentralWidget(table)
        window.resize(table.size())
        window.show()

    def find_coll(self):
        ...

    def find_conn(self):
        ...

    def find_init(self):
        ...

    def find(self):
        pass

    def find_sent(self):
        entered = self.get_entered_word()
        sentences_id = app.get().db.get_sentences_id_by_word(entered)
        sentences = [app.get().db.get_sentence(id_) for id_ in sentences_id]
        window = QtWidgets.QMainWindow(self)
        table = SentenceTableWidget(sentences)
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
