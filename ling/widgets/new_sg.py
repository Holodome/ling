from PyQt5 import QtWidgets, uic

from ling.session import Session
from uis_generated.new_sg import Ui_Dialog

class NewSgDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setupUi(self)
        # uic.loadUi("uis/new_sg.ui", self)
