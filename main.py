# main.py

from modules.logging.logger import setup_logger, set_logging_level, logging
from modules.RSSFeedReaderUI import RSSFeedReaderUI
from PySide6 import QtWidgets as qtw

set_logging_level(logging.DEBUG)  

logger = setup_logger('main')

if __name__ == "__main__":
    app = qtw.QApplication([])
    main_window = RSSFeedReaderUI()
    main_window.show()
    app.exec()
