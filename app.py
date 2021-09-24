from PyQt5 import QtWidgets, uic, QtCore
from ling import *
from table import LingTable


def reformat_text(text):
    result = " ".join(text.split())
    return result


class Application(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("app.ui", self)
        self.init_ui()

        self.parse_state = TextParseState()
        self.is_edit_enabled = False

    def init_ui(self):
        self.setWindowTitle("Linguistics")
        # инциализация выбора типа
        for kind_name in LING_KIND_STRINGS:
            self.kind_selection.addItem(kind_name)

        self.mark_button.clicked.connect(self._do_mark)
        self.input_lock_btn.stateChanged.connect(self._do_input_lock)
        self.open_file_btn.clicked.connect(self._load_from_text_file)
        self.show_result_btn.clicked.connect(self._show_result)
        self.save_btn.clicked.connect(self._save)
        self.open_from_output_btn.clicked.connect(self._load_output)

    def start_edit(self, start, text=None):
        # NOTE(hl): Does not do parse_state initialization!
        if text is None:
            text = self.text_edit.toPlainText()
            self.parse_state.init_for_text(text)
        text = reformat_text(text)

        if start:
            self.is_edit_enabled = True
            self.text_edit.setReadOnly(True)
            self.parse_state.init_for_text(text)
            self.text_edit.setHtml(self.parse_state.html_formatted_text)
            self.input_lock_btn.setChecked(True)
        else:
            self.is_edit_enabled = False
            self.text_edit.setReadOnly(False)
            self.text_edit.setPlainText(text)
            self.input_lock_btn.setChecked(False)

    def _do_input_lock(self):
        is_checked = self.sender().isChecked()
        self.start_edit(is_checked)

    def _do_mark(self):
        if not self.is_edit_enabled:
            self.start_edit(True)

        cursor = self.text_edit.textCursor()
        sel_start = cursor.selectionStart()
        sel_end = cursor.selectionEnd()
        current_mode = LingKind(self.kind_selection.currentIndex())
        if self.parse_state.mark(sel_start, sel_end, current_mode):
            self.text_edit.setHtml(self.parse_state.html_formatted_text)

    def _load_from_text_file(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Open file")[0]
        if filename:
            with open(filename) as file:
                data = file.read()
                data = reformat_text(data)
                self.start_edit(True, data)

    def _show_result(self):
        output = self.parse_state.get_structured_output()
        window = QtWidgets.QMainWindow(self)
        table = LingTable(output.table)
        window.setCentralWidget(table)
        window.resize(table.size())
        window.show()

    def _save(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Save file", filter="*.csv")[0]
        if filename:
            with open(filename, "w") as file:
                struct = self.parse_state.get_structured_output()
                struct.to_csv(file)

    def _load_output(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Open file", filter="*.csv")[0]
        if filename:
            with open(filename) as file:
                struct = StructuredOutput.from_csv(file)
                self.parse_state.init_from_output(struct)
                self.text_edit.setHtml(self.parse_state.html_formatted_text)
