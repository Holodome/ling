import logging

import PyQt5.Qt
from PyQt5 import QtWidgets, uic, QtGui, Qt

import ling.db
from ling import qt_helper
from ling.session import Session
import ling.word
from ling.widgets.db_connection_interface import DbConnectionInterface
from ling.widgets.new_sg import NewSgDialog
from ling.widgets.word_search import WordSearchDialog

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
    "К статистике",
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
    "Статистика"
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
    ["Сочетание", "Семантическая группа", "Число записей", "Число связей", "Число предложений"],
    ["Предикат", "Актант", "Группа актанта", "Число записей", "Число предложений"],
    ["Предложение", "Число слов", "Число сочетаний", "Число связей"],
    ["Число семантических групп", "Число слов", "Число начальных форм", "Число сочетаний", "Число связей",
     "Число предложений"]
]

NAV_MODE_BTNS: List[List[int]] = [
    [NAV_BTN_ADD, NAV_BTN_DELETE, NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_GENERAL],
    [NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_SENT, NAV_BTN_GENERAL],
    [NAV_BTN_WORD, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_SENT, NAV_BTN_GENERAL],
    [NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_CON, NAV_BTN_SENT, NAV_BTN_SG, NAV_BTN_GENERAL],
    [NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_SENT, NAV_BTN_SG, NAV_BTN_GENERAL],
    [NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_ANALYSIS, NAV_BTN_DELETE, NAV_BTN_GENERAL],
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

    def __init__(self, session: Session, make_sent_edit_cb, parent=None):
        super().__init__(parent)
        self.session = session
        self.mode: int
        self.make_sent_edit_cb = make_sent_edit_cb

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

            self.table.setRowCount(1)
            qt_helper.add_table_row(self.table, 0, [
                str(sg_count),
                str(word_count),
                str(init_word_count),
                str(col_count),
                str(con_count),
                str(sent_count),
            ])
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()

    def clear_table_data(self):
        qt_helper.clear_table(self.table)

    def init_ui(self):
        self.search_btn.clicked.connect(lambda: self.decorate(self.search))
        self.table.setEditTriggers(Qt.QTableWidget.NoEditTriggers)
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

    def search(self):
        dialog = WordSearchDialog(self.session, self)
        if dialog.exec_() == PyQt5.Qt.QDialog.Accepted:
            search_str = dialog.input.text()
            if search_str:
                words = self.session.db.get_word_ids_by_word_part(search_str)
                self.display_table_words(self.session.get_words_from_ids(words))

    def display_table_sgs(self, sgs: List[ling.db.SemanticGroup]):
        self.mode_storage = sgs

        self.init_mode(NAV_MODE_SG)
        self.table.setRowCount(len(sgs))
        for idx, sg in enumerate(sgs):
            nwords = len(self.session.get_words_of_sg(sg.id))
            cols = self.session.db.get_cols_of_sg(sg.id)
            ncons = 0
            for col in cols:
                ncons += len(self.session.db.get_con_ids_with_col_id(col))
            ncols = len(cols)
            qt_helper.add_table_row(self.table, idx, [
                sg.name,
                str(nwords),
                str(ncols),
                str(ncons),
            ])
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def display_table_words(self, words: List[ling.db.Word]):
        self.mode_storage = words

        self.init_mode(NAV_MODE_WORD)
        self.table.setRowCount(len(words))
        for idx, word in enumerate(words):
            pos = ling.word.pos_to_russian(word.pos)
            init = self.session.get_initial_form(word)
            print(init, word)
            init = init.word
            # FIXME!!!
            ntimes = 0
            cols = self.session.db.get_col_ids_with_word_id(word.id)
            ncons = 0
            for col in cols:
                ncons += len(self.session.db.get_con_ids_with_col_id(col))
            ncols = len(cols)
            nsents = len(self.session.db.get_sentences_id_by_word_id(word.id))
            qt_helper.add_table_row(self.table, idx, [
                word.word,
                pos,
                init,
                str(ntimes),
                str(ncols),
                str(ncons),
                str(nsents)
            ])
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def display_table_cols(self, cols: List[ling.db.Collocation]):
        self.mode_storage = cols

        self.init_mode(NAV_MODE_COL)
        self.table.setRowCount(len(cols))
        for idx, col in enumerate(cols):
            text = col.text
            sg = self.session.db.get_sg(col.sg_id).name
            # FIXME!!!
            nentr = 0
            ncons = len(self.session.db.get_con_ids_with_col_id(col.id))
            # FIXME!!!
            nsents = 0
            qt_helper.add_table_row(self.table, idx, [
                text,
                sg,
                str(nentr),
                str(ncons),
                str(nsents)
            ])
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def display_table_cons(self, cons: List[ling.db.Connection]):
        self.mode_storage = cons

        self.init_mode(NAV_MODE_CON)
        self.table.setRowCount(len(cons))
        for idx, con in enumerate(cons):
            pred = self.session.db.get_col(con.predicate)
            act = self.session.db.get_col(con.object_)

            pred_str = pred.text
            act_str = act.text
            act_kind = self.session.db.get_sg(act.sg_id).name
            # FIXME:
            nentr = 0
            # FIXME:
            nsent = 0
            qt_helper.add_table_row(self.table, idx, [
                pred_str,
                act_str,
                act_kind,
                str(nentr),
                str(nsent),
            ])
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def display_table_sents(self, sents: List[ling.db.Sentence]):
        self.mode_storage = sents

        self.init_mode(NAV_MODE_SENT)
        self.table.setRowCount(len(sents))
        for idx, sent in enumerate(sents):
            text = sent.contents
            nwords = len(sent.words)
            ncols = len(sent.cols)
            ncons = len(sent.cons)
            qt_helper.add_table_row(self.table, idx, [
                text,
                str(nwords),
                str(ncols),
                str(ncons)
            ])
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def display_table_word_inits(self, words: List[ling.db.Word]):
        self.mode_storage = words

        self.init_mode(NAV_MODE_INIT_WORD)
        self.table.setRowCount(len(words))
        for idx, word in enumerate(words):
            word_str = word.word
            pos = ling.word.pos_to_russian(word.pos)
            # FIXME!!!
            ntimes = 0
            cols = self.session.db.get_col_ids_with_word_id(word.id)
            ncons = 0
            for col in cols:
                ncons += len(self.session.db.get_con_ids_with_col_id(col))
            ncols = len(cols)
            nsents = len(self.session.db.get_sentences_id_by_word_id(word.id))
            qt_helper.add_table_row(self.table, idx, [
                word.word,
                pos,
                str(ntimes),
                str(ncols),
                str(ncons),
                str(nsents)
            ])
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    """
    GENERAL
    """

    def sg_btn_general(self):
        all_sgs = self.session.db.get_all_sgs()
        self.display_table_sgs(all_sgs)

    def word_btn_general(self):
        all_words = self.session.db.get_all_words()
        self.display_table_words(all_words)

    def word_init_btn_general(self):
        all_words = self.session.db.get_all_words()
        init_words = list(filter(lambda it: it.initial_form_id is None, all_words))
        self.display_table_word_inits(init_words)

    def col_btn_general(self):
        all_cols = self.session.db.get_all_cols()
        self.display_table_cols(all_cols)

    def con_btn_general(self):
        all_cons = self.session.db.get_all_cons()
        self.display_table_cons(all_cons)

    def sent_btn_general(self):
        all_sents = self.session.db.get_all_sentences()
        self.display_table_sents(all_sents)

    """
    WORDS
    """

    def word_init_btn_word(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            words = [self.mode_storage[idx]
                     for idx in sel_rows]
            word_inits = list({self.session.db.get_word(word.initial_form_id)
                               for word in words
                               if word.initial_form_id is not None})
            self.display_table_word_inits(word_inits)

    def col_btn_word(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            words = [self.mode_storage[idx]
                     for idx in sel_rows]
            cols = list({col
                         for word in words
                         for col in self.session.db.get_col_ids_with_word_id(word.id)})
            self.display_table_cols(self.session.get_cols_from_ids(cols))

    def con_btn_word(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            words = [self.mode_storage[idx] for idx in sel_rows]
            cols = list({col
                         for word in words
                         for col in self.session.db.get_col_ids_with_word_id(word.id)})
            cons = list({con
                         for col in cols
                         for con in self.session.db.get_con_ids_with_col_id(col)})
            self.display_table_cons(self.session.get_cons_from_ids(cons))

    def sent_btn_word(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            words = [self.mode_storage[idx]
                     for idx in sel_rows]
            sents = list({sent
                          for word in words
                          for sent in self.session.db.get_sentences_id_by_word_id(word.id)})
            self.display_table_sents(self.session.get_sents_from_ids(sents))

    """
    COLS
    """

    def word_btn_col(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            cols = [self.mode_storage[idx]
                    for idx in sel_rows]
            words = list({word
                          for col in cols
                          for word in col.words})
            self.display_table_words(self.session.get_words_from_ids(words))

    def word_init_btn_col(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            cols = [self.mode_storage[idx]
                    for idx in sel_rows]
            words = list({word
                          for col in cols
                          for word in col.words})
            word_inits = list({self.session.db.get_word(word.initial_form_id)
                               for word in self.session.get_words_from_ids(words)
                               if word.initial_form_id is not None})
            self.display_table_word_inits(word_inits)

    def con_btn_col(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            cols = [self.mode_storage[idx]
                    for idx in sel_rows]
            cons = list({con
                         for col in cols
                         for con in self.session.db.get_con_ids_with_col_id(col.id)})
            self.display_table_cons(self.session.get_cons_from_ids(cons))

    def sent_btn_col(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            cols = [self.mode_storage[idx]
                    for idx in sel_rows]
            sents = list({sent
                          for col in cols
                          for word in col.words
                          for sent in self.session.db.get_sentences_id_by_word_id(word)})
            self.display_table_sents(self.session.get_sents_from_ids(sents))

    def sg_btn_col(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            cols = [self.mode_storage[idx] for idx in sel_rows]
            sgs = list({col.sg_id
                        for col in cols})
            self.display_table_sgs(self.session.get_sgs_from_ids(sgs))

    """
    CONS
    """

    def word_btn_con(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            cons = [self.mode_storage[idx] for idx in sel_rows]
            words = list({word
                          for con in cons
                          for col_id in (con.predicate, con.object_)
                          for word in self.session.db.get_col(col_id).words})
            self.display_table_words(self.session.get_words_from_ids(words))

    def word_init_btn_con(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            cons = [self.mode_storage[idx] for idx in sel_rows]
            words = list({word
                          for con in cons
                          for col_id in (con.predicate, con.object_)
                          for word in self.session.db.get_col(col_id).words})
            word_inits = list({self.session.db.get_word(word.initial_form_id)
                               for word in self.session.get_words_from_ids(words)
                               if word.initial_form_id is not None})
            self.display_table_word_inits(word_inits)

    def col_btn_con(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            cons = [self.mode_storage[idx] for idx in sel_rows]
            cols = list({col_id
                         for con in cons
                         for col_id in (con.predicate, con.object_)})
            self.display_table_cols(self.session.get_cols_from_ids(cols))

    def sent_btn_con(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            cons = [self.mode_storage[idx] for idx in sel_rows]
            sents = list({sent
                          for con in cons
                          for col_id in (con.predicate, con.object_)
                          for word in self.session.db.get_col(col_id).words
                          for sent in self.session.db.get_sentences_id_by_word_id(word)})
            self.display_table_sents(self.session.get_sents_from_ids(sents))

    def sg_btn_con(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            cons = [self.mode_storage[idx] for idx in sel_rows]
            sgs = list({self.session.db.get_col(col_id).sg
                        for con in cons
                        for col_id in (con.predicate, con.object_)})
            self.display_table_sgs(self.session.get_sgs_from_ids(sgs))

    """
    SENTS
    """

    def word_btn_sent(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            sents = [self.mode_storage[idx] for idx in sel_rows]
            words = list({word
                          for sent in sents
                          for word in sent.words})
            self.display_table_words(self.session.get_words_from_ids(words))

    def word_init_btn_sent(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            sents = [self.mode_storage[idx] for idx in sel_rows]
            words = list({word
                          for sent in sents
                          for word in sent.words})
            word_inits = list({self.session.db.get_word(word.initial_form_id)
                               for word in self.session.get_words_from_ids(words)
                               if word.initial_form_id is not None})
            self.display_table_word_inits(word_inits)

    def col_btn_sent(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            sents = [self.mode_storage[idx] for idx in sel_rows]
            cols = list({col
                         for sent in sents
                         for col in sent.cols})
            self.display_table_cols(self.session.get_cols_from_ids(cols))

    def con_btn_sent(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            sents = [self.mode_storage[idx] for idx in sel_rows]
            cons = list({con
                         for sent in sents
                         for con in sent.cons})
            self.display_table_cons(self.session.get_cons_from_ids(cons))

    def analysis_btn_sent(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            sents = [self.mode_storage[idx] for idx in sel_rows]
            sent = sents[0]
            ling_sent = self.session.create_sent_ctx_from_db(sent.id)
            self.make_sent_edit_cb(ling_sent)

    """
    SG
    """

    def add_btn_sg(self):
        dialog = NewSgDialog(self.session)
        if dialog.exec_() == PyQt5.Qt.QDialog.Accepted:
            name = dialog.input.text()
            if self.session.db.get_sg_id_by_name(name):
                msg = QtWidgets.QErrorMessage(self)
                msg.showMessage("Семантическая группа '%s' уже существует" % name)
            else:
                self.session.db.add_sg(name)

    def delete_btn_sg(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            sgs = [self.mode_storage[idx] for idx in sel_rows]
            cant_delete = []
            for sg in sgs:
                if self.session.db.get_cols_of_sg(sg.id):
                    cant_delete.append(sg.name)
                else:
                    self.session.db.remove_sg(sg)
            if cant_delete:
                msg = QtWidgets.QErrorMessage(self)
                msg.showMessage("Нельзя удалить семантические группы: %s (к ним привязаны сочетания)")

    def word_btn_sg(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            sgs = [self.mode_storage[idx] for idx in sel_rows]
            words = list({word
                          for sg in sgs
                          for word in self.session.get_words_of_sem_group(sg.id)})
            self.display_table_words(self.session.get_words_from_ids(words))

    def word_init_btn_sg(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            sgs = [self.mode_storage[idx] for idx in sel_rows]
            words = list({word
                          for sg in sgs
                          for word in self.session.get_words_of_sem_group(sg.id)})
            word_inits = list({self.session.db.get_word(word.initial_form_id)
                               for word in self.session.get_words_from_ids(words)
                               if word.initial_form_id is not None})
            self.display_table_word_inits(word_inits)

    def col_btn_sg(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            sgs = [self.mode_storage[idx] for idx in sel_rows]
            sg_ids = [sg.id for sg in sgs]
            cols = list(col
                        for col in self.session.db.get_all_cols()
                        if col.sg_id in sg_ids)
            self.display_table_cols(cols)

    def con_btn_sg(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            sgs = [self.mode_storage[idx] for idx in sel_rows]
            sg_ids = [sg.id for sg in sgs]
            cons = [con
                    for con in self.session.db.get_all_cons()
                    if self.session.db.get_col(con.predicate).sg_id in sg_ids
                    or self.session.db.get_col(con.object_).sg_id in sg_ids]
            self.display_table_cons(cons)

    """
    INIT WORDS
    """

    def word_btn_init_word(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            word_inits = [self.mode_storage[idx] for idx in sel_rows]
            words = list({word
                          for word_init in word_inits
                          for word in self.session.db.get_words_with_initial_form(word_init.id)})
            self.display_table_words(self.session.get_words_from_ids(words))

    def col_btn_init_word(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            word_inits = [self.mode_storage[idx] for idx in sel_rows]
            words = list({word
                          for word_init in word_inits
                          for word in self.session.db.get_words_with_initial_form(word_init.id)})
            cols = list({col
                         for word in words
                         for col in self.session.db.get_col_ids_with_word_id(word.id)})
            self.display_table_cols(self.session.get_cols_from_ids(cols))

    def con_btn_init_word(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            word_inits = [self.mode_storage[idx] for idx in sel_rows]
            words = list({word
                          for word_init in word_inits
                          for word in self.session.db.get_words_with_initial_form(word_init.id)})
            cols = list({col
                         for word in words
                         for col in self.session.db.get_col_ids_with_word_id(word.id)})
            cons = list({con
                         for col in cols
                         for con in self.session.db.get_con_ids_with_col_id(col)})
            self.display_table_cons(self.session.get_cons_from_ids(cons))

    def sent_btn_init_word(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            word_inits = [self.mode_storage[idx] for idx in sel_rows]
            words = list({word
                          for word_init in word_inits
                          for word in self.session.db.get_words_with_initial_form(word_init.id)})
            sents = list({sent
                          for word in words
                          for sent in self.session.db.get_sentences_id_by_word_id(word)})
            self.display_table_sents(self.session.get_sents_from_ids(sents))

    def delete_btn_sent(self):
        sel_rows = qt_helper.table_get_sel_rows(self.table)
        if sel_rows:
            sents = [self.mode_storage[idx] for idx in sel_rows]
            for sent in sents:
                self.session.db.delete_sentence(sent.id)
            new_sents = list(filter(lambda it: it not in sents, self.mode_storage))
            self.display_table_sents(new_sents)

