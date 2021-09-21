from ling import *
from PyQt5 import QtWidgets


class LingTable(QtWidgets.QTableWidget):
    def __init__(self, output, *args):
        super().__init__(*args)
        column_count = LingKind.COUNT.value
        row_count = max(map(len, output))
        self.setRowCount(row_count)
        self.setColumnCount(column_count)
        print(output)
        for col_i, col in enumerate(output):
            for row_i, it in enumerate(col):
                item = QtWidgets.QTableWidgetItem(it)
                self.setItem(row_i, col_i, item)
        self.setHorizontalHeaderLabels(LING_KIND_STRINGS)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()