import logging
import os
import sys
import time


def init_logger():
    logs_folder = "logs"
    if not os.path.exists(logs_folder):
        os.mkdir(logs_folder)
    log_filename = "log_%s.log" % time.asctime()
    log_filepath = os.path.join(logs_folder, log_filename)
    logging.basicConfig(format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG,
                        handlers=[
                            logging.FileHandler(log_filepath),
                            logging.StreamHandler(sys.stdout)
                        ],
                        )
    logging.info("Initialized logging to file '%s'", log_filepath)
    logging.getLogger("PyQt5.uic.uiparser").setLevel(logging.WARN)
    logging.getLogger("PyQt5.uic.properties").setLevel(logging.WARN)

