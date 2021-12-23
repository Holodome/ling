import logging

import PyQt5.Qt
from PyQt5 import QtWidgets, uic

from ling.session import Session
from ling.widgets.db_connection_interface import DbConnectionInterface

# Buttons
NAV_BTN_SG = 0x0
NAV_BTN_WORD = 0x1
NAV_BTN_COL = 0x2
NAV_BTN_CON = 0x3
NAV_BTN_SENT = 0x4
NAV_BTN_CON_WORD = 0x5
NAV_BTN_ADD = 0x6
NAV_BTN_DELETE = 0x7
NAV_BTN_WORD_INIT = 0x8
NAV_BTN_GENERAL = 0x9

NAV_BTN_SENTINEL = NAV_BTN_GENERAL + 1

NAV_BTN_NAMES = [
    "Семантические группы",
    "Слова",
    "Сочетания",
    "Связи",
    "Предложения",
    "Связанные слова",
    "Добавить",
    "Удалить",
    "Начальные формы",
    "Общий вид",
]

NAV_BTN_FUNCTION_NAMES = [
    "sg_btn",
    "word_btn",
    "col_btn",
    "con_btn",
    "sent_btn",
    "con_word_btn",
    "add_btn",
    "delete_btn",
    "word_init_btn",
    "general_btn",
]

NAV_MODE_SG = 0x0
NAV_MODE_WORD = 0x1
NAV_MODE_INIT_WORD = 0x2
NAV_MODE_COL = 0x3
NAV_MODE_CON = 0x4
NAV_MODE_SENT = 0x5
NAV_MODE_GENERAL = 0x6

NAV_MODE_NAMES: list[str] = [
    "Семантические группы",
    "Слова",
    "Однокоренные слова",
    "Сочетания",
    "Связи",
    "Предложения",
    "Общий вид"
]

NAV_MODE_SUFFIXES: list[str] = [
    "_sg",
    "_word",
    "_init_word",
    "_col",
    "_con",
    "_sent",
    "_general"
]

NAV_MODE_HEADERS: list[list[str]] = [
    ["Название", "Число слов", "Число сочетаний", "Число свзяей"],
    ["Слово", "Часть речи", "Начальная форма", "Число записей", "Число сочетаний", "Число связей"],
    ["Слово", "Часть речи", "Число сочетаний", "Число записей", "Число связей"],
    ["Сочетание", "Число записей", "Число связей"],
    ["Предикат", "Актант", "Число записей"],
    ["Предложение"],
    ["Число семантических групп", "Число слов", "Число начальных форм", "Число сочетаний", "Число связей", "Число предложений"]
]

NAV_MODE_BTNS: list[list[int]] = [
    [NAV_BTN_ADD, NAV_BTN_DELETE, NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_CON],
    [NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_SENT],
    [NAV_BTN_WORD, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_SENT],
    [NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_CON, NAV_BTN_SENT, NAV_BTN_SG],
    [NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_SENT, NAV_BTN_SG],
    [NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_CON],
    [NAV_BTN_SG, NAV_BTN_WORD, NAV_BTN_WORD_INIT, NAV_BTN_COL, NAV_BTN_CON, NAV_BTN_SENT]
]


class NavigationWidget(QtWidgets.QWidget, DbConnectionInterface):
    def on_db_connection(self):
        raise NotImplementedError

    def on_db_connection_change(self):
        raise NotImplementedError

    def on_db_connection_loss(self):
        raise NotImplementedError

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.mode: int

        uic.loadUi("uis/navigation.ui", self)

        self.init_ui()
        self.init_mode(NAV_MODE_GENERAL)

    def init_mode(self, mode: int):
        self.table_label.setText(NAV_MODE_NAMES[mode])
        self.buttons.setLayout(self.premade_layouts[mode])
        headers = NAV_MODE_HEADERS[mode]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

    def init_ui(self):
        self.premade_layouts = []
        for idx, (suffix, buttons) in enumerate(zip(NAV_MODE_SUFFIXES, NAV_MODE_BTNS)):
            layout = QtWidgets.QVBoxLayout()
            for button in buttons:
                button_name = NAV_BTN_NAMES[button]
                function_cb_name = NAV_BTN_FUNCTION_NAMES[button] + suffix
                button_function = getattr(self, function_cb_name, None)
                if button_function is None:
                    logging.critical("UNABLE TO FIND FUNCTION %s", function_cb_name)
                button = QtWidgets.QPushButton(button_name)
                button.clicked.connect(lambda: button_function(self))
                layout.addWidget(button)
            self.premade_layouts.append(layout)

    def add_btn_sg(self):
        raise NotImplementedError
        
    def delete_btn_sg(self):
        raise NotImplementedError
        
    def word_btn_sg(self):
        raise NotImplementedError
        
    def word_init_btn_sg(self):
        raise NotImplementedError
        
    def col_btn_sg(self):
        raise NotImplementedError
        
    def con_btn_sg(self):
        raise NotImplementedError
        
    def word_init_btn_word(self):
        raise NotImplementedError
        
    def col_btn_word(self):
        raise NotImplementedError
        
    def con_btn_word(self):
        raise NotImplementedError
        
    def sent_btn_word(self):
        raise NotImplementedError
        
    def word_btn_init_word(self):
        raise NotImplementedError
        
    def col_btn_init_word(self):
        raise NotImplementedError
        
    def con_btn_init_word(self):
        raise NotImplementedError
        
    def sent_btn_init_word(self):
        raise NotImplementedError
        
    def word_btn_col(self):
        raise NotImplementedError
        
    def word_init_btn_col(self):
        raise NotImplementedError
        
    def con_btn_col(self):
        raise NotImplementedError
        
    def sent_btn_col(self):
        raise NotImplementedError
        
    def sg_btn_col(self):
        raise NotImplementedError
        
    def word_btn_con(self):
        raise NotImplementedError
        
    def word_init_btn_con(self):
        raise NotImplementedError
        
    def col_btn_con(self):
        raise NotImplementedError
        
    def sent_btn_con(self):
        raise NotImplementedError
        
    def sg_btn_con(self):
        raise NotImplementedError
        
    def word_btn_sent(self):
        raise NotImplementedError
        
    def word_init_btn_sent(self):
        raise NotImplementedError
        
    def col_btn_sent(self):
        raise NotImplementedError
        
    def con_btn_sent(self):
        raise NotImplementedError
        
    def sg_btn_general(self):
        raise NotImplementedError
        
    def word_btn_general(self):
        raise NotImplementedError
        
    def word_init_btn_general(self):
        raise NotImplementedError
        
    def col_btn_general(self):
        raise NotImplementedError
        
    def con_btn_general(self):
        raise NotImplementedError
        
    def sent_btn_general(self):
        raise NotImplementedError
        