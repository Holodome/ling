from PyQt5 import QtWidgets, uic, QtCore
from ling import *
from table import LingTable


class Application(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("app.ui", self)
        self.init_ui()

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

    def start_edit(self, start, text=None):
        if text is None:
            text = self.text_edit.toPlainText()

        if start:
            self.is_edit_enabled = True
            self.text_edit.setReadOnly(True)
            self.text_edit.setPlainText(text)
            self.parse_state = TextParseState(text)
            self.input_lock_btn.setChecked(True)
        else:
            self.is_edit_enabled = False
            self.text_edit.setReadOnly(False)
            self.text_edit.setPlainText(self.parse_state.text)
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
                self.start_edit(True, data)

    def _show_result(self):
        output = self.parse_state.get_structured_output()
        window = QtWidgets.QMainWindow(self)
        table = LingTable(output)
        window.setCentralWidget(table)
        window.resize(table.size())
        window.show()
