import logging
import os
import sys
import time


def excepthook_override(cls, exception, traceback):
    import traceback as tb
    import tempfile as tf
    f = tf.TemporaryFile("w+")
    tb.print_exception(cls, exception, traceback, file=f)
    f.seek(os.SEEK_SET)
    logging.error("Python exception: %s", f.read())
    # sys.__excepthook__(cls, exception, traceback)


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
    sys.excepthook = excepthook_override
    logging.info("Initialized logging to file '%s'", log_filepath)
    logging.getLogger("PyQt5.uic.uiparser").setLevel(logging.WARN)
    logging.getLogger("PyQt5.uic.properties").setLevel(logging.WARN)

