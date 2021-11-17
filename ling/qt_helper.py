"""
File containing some helper functions

"""
from PyQt5 import QtWidgets


def create_widget_window(widget, parent):
    window = QtWidgets.QMainWindow(parent)
    window.setCentralWidget(widget)
    window.resize(widget.size())
    window.show()


def table_get_selected_rows(table):
    selected_items = table.selectedItems()
    rows = set()
    for item in selected_items:
        item_row = item.row()
        rows.add(item_row)
    return list(rows)
