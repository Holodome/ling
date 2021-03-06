from PyQt5 import QtWidgets, uic

from ling.session import Session
from uis_generated.change_sg_col import Ui_Dialog

class ChangeSGColDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, session: Session, col_str: str, col_sg: int, parent=None):
        super().__init__(parent)
        self.session = session
        self.setupUi(self)
        # uic.loadUi("uis/change_sg_col.ui", self)
        sgs = self.session.get_sg_list()
        self.sgs = sgs
        for name, _ in sgs:
            self.sg_cb.addItem(name)
        self.sg_cb.setCurrentIndex(col_sg)
        self.preview_field.setText(col_str)
