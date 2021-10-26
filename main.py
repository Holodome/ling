import sys
from PyQt5.QtWidgets import QApplication
from ling.app_wdg import AppWidget
from ling import logger



def main():
    logger.init_logger()

    app = QApplication(sys.argv)
    widget = AppWidget()
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()