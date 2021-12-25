from PyQt5 import QtWidgets, uic

from ling.session import Session


class NewSgDialog(QtWidgets.QDialog):
    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        uic.loadUi("uis/new_sg.ui", self)
