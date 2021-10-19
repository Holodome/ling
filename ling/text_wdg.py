from PyQt5 import QtWidgets, uic

from ling import *
from sent_wdg import SentenceEditWidget


class TextEditWidget(QtWidgets.QMainWindow):
    def __init__(self, ctx: TextCtx):
        super().__init__()
        self.ctx = ctx
        self.per_sentence_widgets = {}

        uic.loadUi("../uis/text_edit.ui", self)
        self.init_ui()

    def generate_view(self):
        self.text_view.setPlainText(self.ctx.text)

    def init_ui(self):
        self.edit_sentence_btn.clicked.connect(self.do_edit_sentence)
        self.open_file_btn.clicked.connect(self.do_open_file)
        self.text_view.setReadOnly(True)
        self.generate_view()

    def do_open_file(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Open file")[0]
        if filename:
            with open(filename) as file:
                data = file.read()
                self.ctx.init_for_text(data)
                self.generate_view()

    def do_edit_sentence(self):
        qt_cursor = self.text_view.textCursor()
        cursor_position = qt_cursor.position()
        sentence_idx = self.ctx.get_sentence_idx_from_cursor(cursor_position)
        if sentence_idx != -1:
            widget = self.per_sentence_widgets.get(sentence_idx)
            if widget is not None and widget.isVisible():
                widget.raise_()
            else:
                sentence_ctx = self.ctx.sentence_ctxs[sentence_idx]
                widget = SentenceEditWidget(sentence_ctx, self)
                self.per_sentence_widgets[sentence_idx] = widget
                widget.show()


def test_text_edit():
    import sys

    text_ctx = TextCtx()

    app = QtWidgets.QApplication(sys.argv)
    exec = TextEditWidget(text_ctx)
    exec.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_text_edit()
