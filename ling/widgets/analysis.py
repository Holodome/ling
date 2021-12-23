import PyQt5.Qt
from PyQt5 import QtWidgets, uic

import functools
import logging

import ling.sentence
import ling.text
import ling.qt_helper
from ling.session import Session
from ling.widgets.change_sg_col import ChangeSGColDialog
from ling.widgets.db_connection_interface import DbConnectionInterface
from ling.widgets.delete_words_col import DeleteWordsColDialog


def require(*, session: bool = False, text: bool = False, sent: bool = False):
    if sent:
        session = text = True
    if text:
        session = True

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            assert len(args) >= 1
            self = args[0]
            if session and not self.session.connected:
                msg = QtWidgets.QErrorMessage(self)
                msg.showMessage("Необходима открытая база данных")
                return
            if text and self.text_edit is None:
                msg = QtWidgets.QErrorMessage(self)
                msg.showMessage("Необходим открытый текст")
                return
            if sent and self.sent_edit is None:
                msg = QtWidgets.QErrorMessage(self)
                msg.showMessage("Необходимо выбранное предложение")
                return
            return func(*args, **kwargs)
        return wrapper
    return decorator


class AnalysisWidget(QtWidgets.QWidget, DbConnectionInterface):
    def on_db_connection_change(self):
        pass

    def on_db_connection_loss(self):
        pass

    def __init__(self, session: Session, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.session = session
        self.sent_edit: ling.sentence.Sentence = None
        self.text_edit: ling.text.Text = None
        self.sgs: List[Tuple[str, int]] = []

        uic.loadUi("uis/analysis.ui", self)
        self.init_ui()

    def on_db_connection(self):
        self.init_for_db()

    def init_ui(self):
        if self.session.connected:
            self.init_for_db()

        self.choose_sent_btn.clicked.connect(lambda: self.choose_sent())
        self.load_text_btn.clicked.connect(lambda: self.load_text())
        self.make_col_btn.clicked.connect(lambda: self.make_col())
        self.make_con_btn.clicked.connect(lambda: self.make_con())
        self.add_new_sg_btn.clicked.connect(lambda: self.add_new_sg())
        self.automake_con_btn.clicked.connect(lambda: self.automake_con())
        self.change_sg_col_btn.clicked.connect(lambda: self.change_sg_col())
        self.change_words_col_btn.clicked.connect(lambda: self.change_words_col())
        self.delete_col_btn.clicked.connect(lambda: self.delete_col())
        self.delete_con_btn.clicked.connect(lambda: self.delete_con())
        self.union_col_btn.clicked.connect(lambda: self.union_col())

    def save_changes_to_db(self):
        self.session.db.add_or_update_sentence_record(self.sent_edit)
        logging.info("Saved sentence changes to db")

    def init_for_db(self):
        cb = self.sg_cb
        sgs = self.session.get_sg_list()
        self.sgs = sgs
        for name, _ in sgs:
            cb.addItem(name)

    def init_for_text(self, text_str: str):
        self.text_edit = ling.text.Text(self.session, text_str)
        self.text_field.setPlainText(text_str)

    def init_for_sent(self, sent: str):
        self.sent_edit = ling.sentence.Sentence(self.session, sent)
        self.generate_sent_view()
        self.save_changes_to_db()

    def generate_col_table(self):
        self.col_table.setRowCount(len(self.sent_edit.cols))
        for idx, col in enumerate(self.sent_edit.cols):
            pretty = self.sent_edit.get_pretty_string_with_words_for_col(idx)
            sg_name = self.sgs[col.sg][0]
            print(pretty, sg_name)
            col_it = QtWidgets.QTableWidgetItem(pretty)
            sg_it = QtWidgets.QTableWidgetItem(sg_name)
            self.col_table.setItem(idx, 0, col_it)
            self.col_table.setItem(idx, 1, sg_it)
            # FIXME(hl): QT EATS SPACES IN WIDGET ITEMS!!!!

    def generate_con_table(self):
        self.con_table.setRowCount(len(self.sent_edit.cons))
        for idx, con in enumerate(self.sent_edit.cons):
            pred_pretty = self.sent_edit.get_pretty_string_with_words_for_col(con.predicate_idx)
            actant_pretty = self.sent_edit.get_pretty_string_with_words_for_col(con.actant_idx)
            col_it = QtWidgets.QTableWidgetItem(pred_pretty)
            sg_it = QtWidgets.QTableWidgetItem(actant_pretty)
            self.col_table.setItem(idx, 0, col_it)
            self.col_table.setItem(idx, 1, sg_it)
        self.con_table.resizeColumnsToContents()
        self.con_table.resizeRowsToContents()

    def generate_sent_view(self):
        self.generate_col_table()
        self.generate_con_table()
        html = self.sent_edit.get_colored_html()
        self.sent_field.setHtml(html)

    @require(session=True)
    def load_text(self):
        if self.sent_edit is not None:
            raise NotImplementedError

        text_filename = QtWidgets.QFileDialog.getOpenFileName(self, "Open text (txt)", filter="*.txt")[0]
        if text_filename:
            try:
                with open(text_filename, "r", encoding="utf8") as f:
                    data = f.read()
                    self.init_for_text(data)
            except OSError:
                logging.error("Failed to open file")

    @require(text=True)
    def choose_sent(self):
        qt_cursor = self.text_field.textCursor()
        cursor_position = qt_cursor.position()
        sent_idx = self.text_edit.get_sentence_idx_for_cursor(cursor_position)
        if sent_idx != -1:
            sent_text = self.text_edit.sentences[sent_idx]
            self.init_for_sent(sent_text)
        else:
            logging.info("Selected sentence index is not found")

    @require(sent=True)
    def make_col(self):
        qt_cursor = self.sent_field.textCursor()
        if qt_cursor.hasSelection():
            selection_start = qt_cursor.selectionStart()
            selection_end = qt_cursor.selectionEnd()
            kind = self.sgs[self.sg_cb.currentIndex()][1]
            self.sent_edit.make_col_text_part(selection_start, selection_end, ling.sentence.SemanticGroup(kind))
            self.save_changes_to_db()
            self.generate_sent_view()

    @require(sent=True)
    def change_sg_col(self):
        selected = ling.qt_helper.table_get_selected_rows(self.col_table)
        if selected:
            selected = selected[0]
            dialog = ChangeSGColDialog(self.session, self.sent_edit.get_pretty_string_with_words_for_col(selected),
                                       self.sent_edit.cols[selected].sg, self)
            if dialog.exec_() == PyQt5.Qt.QDialog.Accepted:
                dialog_selected = dialog.sg_cb.currentIndex()
                self.sent_edit.change_semantic_group_for_col(selected, dialog_selected)
                self.save_changes_to_db()
                self.generate_sent_view()

    @require(sent=True)
    def change_words_col(self):
        selected = ling.qt_helper.table_get_selected_rows(self.col_table)
        if selected:
            selected = selected[0]
            dialog = DeleteWordsColDialog(self.session, self.sent_edit.get_pretty_string_with_words_for_col(selected),
                                          [self.sent_edit.words[it] for it in self.sent_edit.cols[selected].word_idxs],
                                          self)
            if dialog.exec_() == PyQt5.Qt.QDialog.Accepted:
                dialog_selected = [it.row() for it in dialog.word_list.selectionModel().selectedIndexes()]
                self.sent_edit.remove_words_from_col(selected, dialog_selected)
                self.save_changes_to_db()
                self.generate_sent_view()

    @require(sent=True)
    def delete_col(self):
        selected = ling.qt_helper.table_get_selected_rows(self.col_table)
        if selected:
            dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Удаление", "Удалить?",
                                           QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if dialog.exec_() == QtWidgets.QMessageBox.Yes:
                self.sent_edit.remove_cols(selected)
                self.save_changes_to_db()
                self.generate_sent_view()

    @require(sent=True)
    def union_col(self):
        selected = ling.qt_helper.table_get_selected_rows(self.col_table)
        if len(selected) >= 2:
            dialog = ChangeSGColDialog(self.session, self.sent_edit.get_pretty_string_with_words_for_cols(selected),
                                       self.sent_edit.cols[selected[0]].sg, self)
            if dialog.exec_() == PyQt5.Qt.QDialog.Accepted:
                dialog_selected_sg = dialog.sg_cb.currentIndex()
                self.sent_edit.join_cols(selected, dialog_selected_sg)
                self.save_changes_to_db()
                self.generate_sent_view()

    @require(sent=True)
    def make_con(self):
        selected = ling.qt_helper.table_get_selected_rows(self.col_table)
        self.sent_edit.make_con_from_list(selected)
        self.save_changes_to_db()
        self.generate_sent_view()

    @require(sent=True)
    def delete_con(self):
        selected = ling.qt_helper.table_get_selected_rows(self.con_table)
        if selected:
            dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Удаление", "Удалить?",
                                           QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if dialog.exec_() == QtWidgets.QMessageBox.Yes:
                self.sent_edit.remove_cons(selected)
                self.save_changes_to_db()
                self.generate_sent_view()

    @require(sent=True)
    def automake_con(self):
        self.sent_edit.make_default_cons()

    @require(sent=True)
    def add_new_sg(self):
        raise NotImplementedError

