def table_get_selected_rows(table):
    selected_items = table.selectedItems()
    rows = set()
    for item in selected_items:
        item_row = item.row()
        rows.add(item_row)
    return list(rows)


def clear_table(table):
    while table.rowCount():
        table.removeRow(0)
