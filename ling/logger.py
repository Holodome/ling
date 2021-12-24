import logging
import os
import sys
import time
import traceback as tb
import tempfile as tf

LOG_COUNT_MARGIN = 100


def excepthook_override(cls, exception, traceback):
    f = tf.TemporaryFile("w+")
    tb.print_exception(cls, exception, traceback, file=f)
    f.seek(os.SEEK_SET)
    logging.error("Python exception: %s", f.read())


def init_logger():
    home_folder = os.path.expanduser("~")
    logs_folder = os.path.join(home_folder, ".ling_logs")
    if not os.path.exists(logs_folder):
        os.mkdir(logs_folder)
    # Check if we need to cleanup a bit
    logs = os.listdir(logs_folder)
    if len(logs) > LOG_COUNT_MARGIN:
        logs.sort(reverse=True)
        while len(logs) > LOG_COUNT_MARGIN:
            os.remove(os.path.join(logs_folder, logs.pop()))

    log_filename = "log_%d.log" % time.time()
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

