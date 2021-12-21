from PyQt5 import QtWidgets, uic

from ling.session import Session


class ChangeSGColDialog(QtWidgets.QDialog):
    def __init__(self, session: Session, col_str: str, col_sg: int, parent=None):
        super().__init__(parent)
        self.session = session
        uic.loadUi("uis/change_sg_col.ui", self)
        sgs = self.session.get_sg_list()
        self.sgs = sgs
        for name, _ in sgs:
            self.sg_cb.addItem(name)
        self.sg_cb.setCurrentIndex(col_sg)
        self.preview_field.setText(col_str)
