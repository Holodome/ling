from PyQt5 import QtWidgets, uic, QtCore
from ling import *


class SentenceEditWidget(QtWidgets.QMainWindow):
    def __init__(self, ctx: SentenceCtx):
        super().__init__()
        self.ctx = ctx

        uic.loadUi("uis/sentence_edit.ui", self)
        self.init_ui()

    def generate_table(self):
        table = self.collocations_tb
        table.setRowCount(len(self.ctx.collocations))
        table.setColumnCount(3)
        for row_idx, collocation in enumerate(self.ctx.collocations):
            word_it = QtWidgets.QTableWidgetItem(str(collocation.words))
            kind_it = QtWidgets.QTableWidgetItem(LING_KIND_STRINGS[collocation.kind.value])
            table.setItem(row_idx, 0, word_it)
            table.setItem(row_idx, 1, kind_it)

    def generate_view(self):
        self.generate_table()
        self.text_view.setHtml(self.ctx.get_funny_html())

    def init_ui(self):
        self.mark_btn.clicked.connect(self.do_mark_btn)
        for kind_name in LING_KIND_STRINGS:
            self.mark_kind_cb.addItem(kind_name)

        self.text_view.setReadOnly(True)
        self.generate_view()

    def do_mark_btn(self):
        qt_cursor = self.text_view.textCursor()
        selection_start = qt_cursor.selectionStart()
        selection_end = qt_cursor.selectionEnd()
        kind_idx = self.mark_kind_cb.currentIndex()
        kind = LingKind(kind_idx)
        self.ctx.mark_text_part(selection_start, selection_end, kind)
        self.generate_view()


def test_sentence_edit():
    import sys

    text = "Летчик пилотировал самолет боковой ручкой управления в плохую погоду. Мама мыла Милу мылом."
    text_ctx = TextCtx()
    text_ctx.init_for_text(text)

    sentence1 = text_ctx.start_sentence_edit(10)
    sentence1.add_collocation([0, 1, 2], LingKind.OBJECT)
    sentence1.mark_text_part(20, 40, LingKind.PREDICATE)

    app = QtWidgets.QApplication(sys.argv)
    exec = SentenceEditWidget(sentence1)
    exec.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_sentence_edit()