import PyQt5.Qt
from PyQt5 import QtWidgets, uic

from ling.session import Session
from ling.widgets.db_connection_interface import DbConnectionInterface


class NavigationWidget(QtWidgets.QWidget, DbConnectionInterface):
    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session