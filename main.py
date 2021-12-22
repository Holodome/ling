import sys
from PyQt5.QtWidgets import QApplication

from ling.session import Session
import ling.widgets.window
from ling import logger


def main():
    logger.init_logger()

    app = QApplication(sys.argv)
    session = Session()
    widget = ling.widgets.window.Window(session)
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
