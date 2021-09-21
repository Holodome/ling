from PyQt5 import QtWidgets, uic
from ling import *


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

    def _do_input_lock(self):
        is_checked = self.sender().isChecked()
        if is_checked:
            self.is_edit_enabled = True
            self.text_edit.setReadOnly(True)
            text = self.text_edit.toPlainText()
            self.parse_state = TextParseState(text)
        else:
            self.is_edit_enabled = False
            self.text_edit.setReadOnly(False)
            self.text_edit.setPlainText(self.parse_state.text)

    def _do_mark(self):
        if not self.is_edit_enabled:
            return

        cursor = self.text_edit.textCursor()
        sel_start = cursor.selectionStart()
        sel_end = cursor.selectionEnd()
        current_mode = LingKind(self.kind_selection.currentIndex() + 1)
        if self.parse_state.mark(sel_start, sel_end, current_mode):
            self.text_edit.setHtml(self.parse_state.html_formatted_text)
            print(self.parse_state.get_structured_output())