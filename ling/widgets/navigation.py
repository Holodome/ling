import logging

import PyQt5.Qt
from PyQt5 import QtWidgets, uic

import ling.db
from ling import qt_helper
from ling.session import Session
import ling.word
from ling.widgets.db_connection_interface import DbConnectionInterface

from typing import List

# Buttons
NAV_BTN_SG = 0x0
NAV_BTN_WORD = 0x1
NAV_BTN_COL = 0x2
NAV_BTN_CON = 0x3
NAV_BTN_SENT = 0x4
NAV_BTN_CON_WORD = 0x5
NAV_BTN_ADD = 0x6
NAV_BTN_DELETE = 0x7
NAV_BTN_WORD_INIT = 0x8
NAV_BTN_GENERAL = 0x9
NAV_BTN_ANALYSIS = 0xA

NAV_BTN_NAMES = [
    "Семантические группы",
    "Слова",
    "Сочетания",
    "Связи",
    "Предложения",
    "Связанные слова",
    "Добавить",
    "Удалить",
    "Начальные формы",
    "Общий вид",
    "К анализу"
]

NAV_BTN_FUNCTION_NAMES = [
    "sg_btn",
    "word_btn",
    "col_btn",
    "con_btn",
    "sent_btn",
    "con_word_btn",
    "add_btn",
    "delete_btn",
    "word_init_btn",
    "general_btn",
    "analysis_btn"
]

NAV_MODE_SG = 0x0
NAV_MODE_WORD = 0x1
NAV_MODE_INIT_WORD = 0x2
NAV_MODE_COL = 0x3
NAV_MODE_CON = 0x4
NAV_MODE_SENT = 0x5
NAV_MODE_GENERAL = 0x6

NAV_MODE_NAMES: List[str] = [
    "Семантические группы",
    "Слова",
    "Однокоренные слова",
    "Сочетания",
    "Связи",
    "Предложения",
    "Общий вид"
]

NAV_MODE_SUFFIXES: List[str] = [
    "_sg",
    "_word",
    "_init_word",
    "_col",
    "_con",
    "_sent",
    "_general"
]

NAV_MODE_HEADERS: List[List[str]] = [
    ["Название", "Число слов", "Число сочетаний", "Число связей"],
    ["Слово", "Часть речи", "Начальная форма", "Число записей", "Число сочетаний", "Число связей", "Число предложений"],
    ["Слово", "Часть речи", "Число сочетаний", "Число записей", "Число связей"],
    ["Сочетание", "Число записей", "Число связей"],
    ["Предикат", "Актант", "Число записей"],
    ["Предложение"],
    ["Число семантических групп", "Число слов", "Число начальных форм", "Число сочетаний", "Число связей", "Число предложений"]
]

NAV_MODE_BTNS: List[List[int]] = [
    [NAV_BTN_ADD, NAV_BTN_DELETE, NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_GENERAL],
    [NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_SENT, NAV_BTN_GENERAL],
    [NAV_BTN_WORD, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_SENT, NAV_BTN_GENERAL],
    [NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_CON, NAV_BTN_SENT, NAV_BTN_SG, NAV_BTN_GENERAL],
    [NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_SENT, NAV_BTN_SG, NAV_BTN_GENERAL],
    [NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_ANALYSIS, NAV_BTN_GENERAL],
    [NAV_BTN_SG, NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_SENT]
]


class NavigationWidget(QtWidgets.QWidget, DbConnectionInterface):
    def on_db_connection(self):
        self.init_mode(NAV_MODE_GENERAL)

    def on_db_connection_loss(self):
        self.clear_table_data()

    def decorate(self, func):
        if not self.session.connected:
            msg = QtWidgets.QErrorMessage(self)
            msg.showMessage("Необходима открытая база данных")
            return
        return func()

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.mode: int

        uic.loadUi("uis/navigation.ui", self)

        self.init_ui()
        self.init_mode(NAV_MODE_GENERAL)

    def init_mode(self, mode: int):
        self.table_label.setText(NAV_MODE_NAMES[mode])
        self.stacked.setCurrentIndex(mode)
        headers = NAV_MODE_HEADERS[mode]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        if mode == NAV_MODE_GENERAL and self.session.connected:
            sg_count = len(self.session.db.get_all_sgs())
            all_words = self.session.db.get_all_words()
            word_count = len(all_words)
            init_word_count = sum(map(lambda it: it.initial_form_id is None, all_words))
            col_count = len(self.session.db.get_all_cols())
            con_count = len(self.session.db.get_all_cons())
            sent_count = len(self.session.db.get_all_sentences())

            sg_it = QtWidgets.QTableWidgetItem(str(sg_count))
            word_it = QtWidgets.QTableWidgetItem(str(word_count))
            wordi_it = QtWidgets.QTableWidgetItem(str(init_word_count))
            col_it = QtWidgets.QTableWidgetItem(str(col_count))
            con_it = QtWidgets.QTableWidgetItem(str(con_count))
            sent_it = QtWidgets.QTableWidgetItem(str(sent_count))
            self.table.setRowCount(1)
            self.table.setItem(0, 0, sg_it)
            self.table.setItem(0, 1, word_it)
            self.table.setItem(0, 2, wordi_it)
            self.table.setItem(0, 3, col_it)
            self.table.setItem(0, 4, con_it)
            self.table.setItem(0, 5, sent_it)
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()

    def clear_table_data(self):
        qt_helper.clear_table(self.table)

    def init_ui(self):
        self.stacked = QtWidgets.QStackedWidget()
        for idx, (suffix, buttons) in enumerate(zip(NAV_MODE_SUFFIXES, NAV_MODE_BTNS)):
            layout = QtWidgets.QVBoxLayout()
            for button in buttons:
                button_name = NAV_BTN_NAMES[button]
                if button != NAV_BTN_GENERAL:
                    function_cb_name = NAV_BTN_FUNCTION_NAMES[button] + suffix
                    button_function = getattr(self, function_cb_name, None)
                    if button_function is None:
                        logging.critical("UNABLE TO FIND FUNCTION %s", function_cb_name)
                else:
                    button_function = lambda: self.init_mode(NAV_MODE_GENERAL)
                print(button_name)
                button = QtWidgets.QPushButton(button_name)

                def build_lambda(a, b):
                    def wrapper():
                        return a(b)
                    return wrapper
                button.clicked.connect(build_lambda(self.decorate, button_function))
                layout.addWidget(button)
            widget = QtWidgets.QWidget()
            widget.setLayout(layout)
            self.stacked.addWidget(widget)
        self.buttons.addWidget(self.stacked)

    def populate_sgs(self, sgs: List[ling.db.SemanticGroup]):
        self.init_mode(NAV_MODE_SG)
        self.table.setRowCount(len(sgs))
        for idx, sg in enumerate(sgs):
            nwords = len(self.session.get_words_of_sem_group(sg.id))
            cols = self.session.db.get_cols_of_sem_group(sg.id)
            ncons = 0
            for col in cols:
                ncons += len(self.session.db.get_con_ids_with_coll_id(col))
            ncols = len(cols)

            name_it = QtWidgets.QTableWidgetItem(sg.name)
            words_it = QtWidgets.QTableWidgetItem(str(nwords))
            cols_it = QtWidgets.QTableWidgetItem(str(ncols))
            cons_it = QtWidgets.QTableWidgetItem(str(ncons))
            self.table.setItem(idx, 0, name_it)
            self.table.setItem(idx, 1, words_it)
            self.table.setItem(idx, 2, cols_it)
            self.table.setItem(idx, 3, cons_it)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def populate_words(self, words: List[ling.db.Word]):
        self.init_mode(NAV_MODE_WORD)
        self.table.setRowCount(len(words))
        for idx, word in enumerate(words):
            pos = ling.word.pos_to_russian(word.pos)
            init = self.session.get_initial_form(word).word
            # FIXME:
            ntimes = 0
            cols = self.session.db.get_col_ids_with_word_id(word.id)
            ncons = 0
            for col in cols:
                ncons += len(self.session.db.get_con_ids_with_coll_id(col))
            ncols = len(cols)
            nsents = len(self.session.db.get_sentences_id_by_word_id(word.id))
            word_it = QtWidgets.QTableWidgetItem(word.word)
            pos_it = QtWidgets.QTableWidgetItem(pos)
            init_it = QtWidgets.QTableWidgetItem(init)
            entr_it = QtWidgets.QTableWidgetItem(str(ntimes))
            cols_it = QtWidgets.QTableWidgetItem(str(ncols))
            cons_it = QtWidgets.QTableWidgetItem(str(ncons))
            sents_it = QtWidgets.QTableWidgetItem(str(nsents))
            self.table.setItem(idx, 0, word_it)
            self.table.setItem(idx, 1, pos_it)
            self.table.setItem(idx, 2, init_it)
            self.table.setItem(idx, 3, entr_it)
            self.table.setItem(idx, 4, cols_it)
            self.table.setItem(idx, 5, cons_it)
            self.table.setItem(idx, 6, sents_it)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def populate_cols(self, cols: List[ling.db.Collocation]):
        self.init_mode(NAV_MODE_SG)
        self.table.setRowCount(len(sgs))
        for idx, sg in enumerate(sgs):
            nwords = len(self.session.get_words_of_sem_group(sg.id))
            cols = self.session.db.get_cols_of_sem_group(sg.id)
            ncons = 0
            for col in cols:
                ncons += len(self.session.db.get_con_ids_with_coll_id(col))
            ncols = len(cols)

            name_it = QtWidgets.QTableWidgetItem(sg.name)
            words_it = QtWidgets.QTableWidgetItem(str(nwords))
            cols_it = QtWidgets.QTableWidgetItem(str(ncols))
            cons_it = QtWidgets.QTableWidgetItem(str(ncons))
            self.table.setItem(idx, 0, name_it)
            self.table.setItem(idx, 1, words_it)
            self.table.setItem(idx, 2, cols_it)
            self.table.setItem(idx, 3, cons_it)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def populate_cons(self, cons: List[ling.db.Connection]):
        self.init_mode(NAV_MODE_SG)
        self.table.setRowCount(len(sgs))
        for idx, sg in enumerate(sgs):
            nwords = len(self.session.get_words_of_sem_group(sg.id))
            cols = self.session.db.get_cols_of_sem_group(sg.id)
            ncons = 0
            for col in cols:
                ncons += len(self.session.db.get_con_ids_with_coll_id(col))
            ncols = len(cols)

            name_it = QtWidgets.QTableWidgetItem(sg.name)
            words_it = QtWidgets.QTableWidgetItem(str(nwords))
            cols_it = QtWidgets.QTableWidgetItem(str(ncols))
            cons_it = QtWidgets.QTableWidgetItem(str(ncons))
            self.table.setItem(idx, 0, name_it)
            self.table.setItem(idx, 1, words_it)
            self.table.setItem(idx, 2, cols_it)
            self.table.setItem(idx, 3, cons_it)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def populate_sents(self, sents: List[ling.db.Sentence]):
        self.init_mode(NAV_MODE_SG)
        self.table.setRowCount(len(sgs))
        for idx, sg in enumerate(sgs):
            nwords = len(self.session.get_words_of_sem_group(sg.id))
            cols = self.session.db.get_cols_of_sem_group(sg.id)
            ncons = 0
            for col in cols:
                ncons += len(self.session.db.get_con_ids_with_coll_id(col))
            ncols = len(cols)

            name_it = QtWidgets.QTableWidgetItem(sg.name)
            words_it = QtWidgets.QTableWidgetItem(str(nwords))
            cols_it = QtWidgets.QTableWidgetItem(str(ncols))
            cons_it = QtWidgets.QTableWidgetItem(str(ncons))
            self.table.setItem(idx, 0, name_it)
            self.table.setItem(idx, 1, words_it)
            self.table.setItem(idx, 2, cols_it)
            self.table.setItem(idx, 3, cons_it)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    """
    GENERAL
    """

    def sg_btn_general(self):
        all_sgs = self.session.db.get_all_sgs()
        self.populate_sgs(all_sgs)

    def word_btn_general(self):
        all_words = self.session.db.get_all_words()
        self.populate_words(all_words)

    def word_init_btn_general(self):
        all_words = self.session.db.get_all_words()
        init_words = list(filter(lambda it: it.initial_form_id is None, all_words))
        raise NotImplementedError

    def col_btn_general(self):
        all_cols = self.session.db.get_all_cols()
        self.populate_cols(all_cols)

    def con_btn_general(self):
        all_cons = self.session.db.get_all_cons()
        self.populate_cons(all_cons)

    def sent_btn_general(self):
        all_sents = self.session.db.get_all_sentences()
        self.populate_sents(all_sents)

    """
    SG
    """

    def add_btn_sg(self):
        raise NotImplementedError
        
    def delete_btn_sg(self):
        raise NotImplementedError
        
    def word_btn_sg(self):
        raise NotImplementedError
        
    def word_init_btn_sg(self):
        raise NotImplementedError
        
    def col_btn_sg(self):
        raise NotImplementedError
        
    def con_btn_sg(self):
        raise NotImplementedError
        
    def word_init_btn_word(self):
        raise NotImplementedError
        
    def col_btn_word(self):
        raise NotImplementedError
        
    def con_btn_word(self):
        raise NotImplementedError
        
    def sent_btn_word(self):
        raise NotImplementedError
        
    def word_btn_init_word(self):
        raise NotImplementedError
        
    def col_btn_init_word(self):
        raise NotImplementedError
        
    def con_btn_init_word(self):
        raise NotImplementedError
        
    def sent_btn_init_word(self):
        raise NotImplementedError
        
    def word_btn_col(self):
        raise NotImplementedError
        
    def word_init_btn_col(self):
        raise NotImplementedError
        
    def con_btn_col(self):
        raise NotImplementedError
        
    def sent_btn_col(self):
        raise NotImplementedError
        
    def sg_btn_col(self):
        raise NotImplementedError
        
    def word_btn_con(self):
        raise NotImplementedError
        
    def word_init_btn_con(self):
        raise NotImplementedError
        
    def col_btn_con(self):
        raise NotImplementedError
        
    def sent_btn_con(self):
        raise NotImplementedError
        
    def sg_btn_con(self):
        raise NotImplementedError
        
    def word_btn_sent(self):
        raise NotImplementedError
        
    def word_init_btn_sent(self):
        raise NotImplementedError
        
    def col_btn_sent(self):
        raise NotImplementedError
        
    def con_btn_sent(self):
        raise NotImplementedError

    def analysis_btn_sent(self):
        raise NotImplementedError