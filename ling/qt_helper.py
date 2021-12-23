from PyQt5 import QtWidgets


def table_get_sel_rows(table):
    selected_items = table.selectedItems()
    rows = set()
    for item in selected_items:
        item_row = item.row()
        rows.add(item_row)
    return list(rows)


def clear_table(table):
    while table.rowCount():
        table.removeRow(0)


def add_table_row(table, row_idx, items):
    for idx, entry in enumerate(items):
        it = QtWidgets.QTableWidgetItem(entry)
        table.setItem(row_idx, idx, it)
