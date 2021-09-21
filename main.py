import sys 
from PyQt5.QtWidgets import QApplication
from app import Application


def excepthook_override(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def main():
    sys.excepthook = excepthook_override
    app = QApplication(sys.argv)
    exec = Application()
    exec.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()