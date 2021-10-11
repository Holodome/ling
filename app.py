from PyQt5 import QtWidgets, uic, QtCore
from ling import *


class SentenceEditWidget(QtWidgets.QMainWindow):
    def __init__(self, ctx: SentenceCtx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.is_view_detailed = False

        uic.loadUi("uis/sentence_edit.ui", self)
        self.init_ui()

    def generate_connections_list(self):
        clist = self.connections_list
        # clear (qt *really* is something..)
        while clist.count():
            clist.takeItem(0)
        for connection in self.ctx.connections:
            clist.addItem(str(connection))

    def generate_table(self):
        table = self.collocations_tb
        table.setRowCount(len(self.ctx.collocations))
        table.setColumnCount(2)
        for row_idx, collocation in enumerate(self.ctx.collocations):
            collocation_words = ";".join(map(lambda it: self.ctx.words[it], collocation.words))
            word_it = QtWidgets.QTableWidgetItem(collocation_words)
            kind_it = QtWidgets.QTableWidgetItem(LING_KIND_STRINGS[collocation.kind.value])
            table.setItem(row_idx, 0, word_it)
            table.setItem(row_idx, 1, kind_it)

    def generate_view(self):
        self.generate_connections_list()
        self.generate_table()
        if self.is_view_detailed:
            # TODO(hl): Not implemented!!! If we display this as plain text, editing becomes a problem because we
            #  would have to remap indices from cursor
            html = self.ctx.get_funny_html_detailed()
        else:
            html = self.ctx.get_funny_html()
        self.text_view.setHtml(html)

    def init_ui(self):
        self.mark_btn.clicked.connect(self.do_mark)
        self.mark_soft_btn.clicked.connect(self.do_mark_soft)
        self.delete_col_btn.clicked.connect(self.do_delete_col)
        self.join_col_btn.clicked.connect(self.do_join_col)
        self.change_kind_btn.clicked.connect(self.do_change_kind)
        self.make_con_btn.clicked.connect(self.do_make_con)
        self.delete_con_btn.clicked.connect(self.do_delete_con)
        for kind_name in LING_KIND_STRINGS:
            self.mark_kind_cb.addItem(kind_name)

        self.text_view.setReadOnly(True)
        self.generate_view()

    def do_mark_internal(self, is_soft):
        qt_cursor = self.text_view.textCursor()
        if qt_cursor.hasSelection():
            selection_start = qt_cursor.selectionStart()
            selection_end = qt_cursor.selectionEnd()
            kind = self.get_selected_ling_kind()
            if is_soft:
                self.ctx.mark_text_part_soft(selection_start, selection_end, kind)
            else:
                self.ctx.mark_text_part(selection_start, selection_end, kind)
            self.generate_view()

    def do_mark_soft(self):
        self.do_mark_internal(True)

    def do_mark(self):
        self.do_mark_internal(False)

    def get_selected_ling_kind(self):
        kind_idx = self.mark_kind_cb.currentIndex()
        kind = LingKind(kind_idx)
        return kind

    def get_list_of_selected_col_table_rows(self):
        selected_items = self.collocations_tb.selectedItems()
        rows = set()
        for item in selected_items:
            item_row = item.row()
            rows.add(item_row)
        return list(rows)

    def do_delete_col(self):
        rows_to_delete = self.get_list_of_selected_col_table_rows()
        self.ctx.remove_collocations(rows_to_delete)
        self.generate_view()

    def do_join_col(self):
        rows_to_join = self.get_list_of_selected_col_table_rows()
        self.ctx.join_collocations(rows_to_join)
        self.generate_view()

    def do_change_kind(self):
        # item = self.collocations_tb.currentItem()
        # HACK(hl): But this is probably the expected behaviour
        rows = self.get_list_of_selected_col_table_rows()
        for row in rows:
            kind = self.get_selected_ling_kind()
            self.ctx.change_kind(row, kind)
            self.generate_view()

    def get_list_of_selected_cons(self):
        selected_items = self.connections_list.selectedItems()
        result = []
        for it in selected_items:
            it_idx = self.connections_list.row(it)
            result.append(it_idx)
        return result

    def do_make_con(self):
        rows_to_connect = self.get_list_of_selected_col_table_rows()
        if len(rows_to_connect) == 2:  # TODO(hl): @UX Warn on this
            self.ctx.make_connection(rows_to_connect[0], rows_to_connect[1])
            self.generate_view()

    def do_delete_con(self):
        items_to_delete = self.get_list_of_selected_cons()
        self.ctx.delete_connections(items_to_delete)
        self.generate_view()


class TextEditWidget(QtWidgets.QMainWindow):
    def __init__(self, ctx: TextCtx):
        super().__init__()
        self.ctx = ctx
        self.per_sentence_widgets = {}

        uic.loadUi("uis/text_edit.ui", self)
        self.init_ui()

    def generate_view(self):
        self.text_view.setPlainText(self.ctx.text)

    def init_ui(self):
        self.edit_sentence_btn.clicked.connect(self.do_edit_sentence)
        self.text_view.setReadOnly(True)
        self.generate_view()

    def do_edit_sentence(self):
        qt_cursor = self.text_view.textCursor()
        cursor_position = qt_cursor.position()
        sentence_idx = self.ctx.get_sentence_idx_from_cursor(cursor_position)
        widget = self.per_sentence_widgets.get(sentence_idx)
        if widget is not None and widget.isVisible():
            widget.raise_()
        else:
            sentence_ctx = self.ctx.sentence_ctxs[sentence_idx]
            widget = SentenceEditWidget(sentence_ctx, self)
            self.per_sentence_widgets[sentence_idx] = widget
            widget.show()



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


def test_text_edit():
    import sys

    text = "Летчик пилотировал самолет боковой ручкой управления в плохую погоду. Мама мыла Милу мылом."
    text_ctx = TextCtx()
    text_ctx.init_for_text(text)

    app = QtWidgets.QApplication(sys.argv)
    exec = TextEditWidget(text_ctx)
    exec.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_text_edit()
