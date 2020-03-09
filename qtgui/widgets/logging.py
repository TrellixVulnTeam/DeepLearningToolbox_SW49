import os
import threading
import logging
logger = logging.getLogger(__name__)

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QPlainTextEdit

from util.error import protect

class QLogHandler(QPlainTextEdit, logging.Handler):
    """A log handler that displays log messages in a QWidget.

    A :py:class:`QLogHandler` can be used 
    """

    _message_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)
        logging.Handler.__init__(self)
        self.setReadOnly(True)
        self._records = []
        self._counter = 1
        self._message_signal.connect(self.appendMessage)
        self._message_signal.emit("Log view initialized")

    def __len__(self):
        """The number of lines in this QLogHandler.
        """
        return self._counter

    def clear(self):
        """Clear this :py:class:QLogHandler.
        """
        super().clear()
        self._records.clear()
        self._counter = 1
        self._message_signal.emit("Log view cleared")

    @pyqtSlot(str)
    def appendMessage(self, message: str):
        message = message.replace(os.linesep, '\\n')
        self.appendPlainText(message)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def emit(self, record: logging.LogRecord) -> None:
        """Handle a :py:class:logging.logRecord.
        """
        # Here we have to be careful: adding the text directly to the
        # widget from another thread causes problems: The program
        # crashes with the following message:
        #   QObject::connect: Cannot queue arguments of type 'QTextBlock'
        #   (Make sure 'QTextBlock' is registered using qRegisterMetaType().)
        # Hence we are doing this via a signal now.        
        self._counter += 1
        self.setToolTip(f"List of log records ({self._counter} entries)")
        try:
            self._records.append(record)
            self._message_signal.emit(self.format(record))
        except AttributeError as error:
            # FIXME[bug/problem]
            # When quitting the program while running some background
            # thread (e.g. camera loop), we get the following exception:
            # AttributeError: 'QLogHandler' does not have a signal with
            #                 the signature _message_signal(QString)
            #print(error)
            #print(f"  type of record: {type(record)}")
            #print(f"  record: {record}")
            #print(f"  signal: {self._message_signal}")
            pass

    @protect
    def mouseReleaseEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        block = cursor.blockNumber()
        print(block, len(self._records))
        if block < len(self._records):
            print(self._records[block])
            record = self._records[block]
            logger.info(f"Trying to open file {record.pathname}, "
                        f"line {record.lineno}, in an external editor.")
            try:
                retcode = util.debugging.edit(record.pathname, record.lineno)
                if retcode < 0:
                    logger.error("Edit command was terminated by signal "
                                 f"{-retcode}")
                else:
                    logger.info(f"Edit command returned: {retcode}")
            except OSError as error:
                logger.error(f"Edit command failed: {error}")


from PyQt5.QtWidgets import QPlainTextEdit
import traceback
import util.debugging

class QExceptionView(QPlainTextEdit):
    """A view for Python exceptions.
    This is basically a text field in which an exception can be
    displayed.

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setReadOnly(True)
        self._exception = None

    def setException(self, exception: BaseException) -> None:
        self._exception = exception
        self._traceback = traceback.extract_tb(exception.__traceback__)
        # _traceback is basicall a list of traceback.FrameSummary,
        # each providing the following attributes:
        #  - filename
        #  - line
        #  - lineno
        #  - locals
        #  - name
        self.clear()
        for m in traceback.format_list(self._traceback):
            self.appendPlainText(m)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    @protect
    def mouseReleaseEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        frame_number = cursor.blockNumber() // 2

        if frame_number < len(self._traceback):
            frame = self._traceback[frame_number]
            logger.info(f"Trying to open file {frame.filename}, "
                        f"line {frame.lineno}, in an external editor.")
            try:
                retcode = util.debugging.edit(frame.filename, frame.lineno)
                if retcode < 0:
                    logger.error("Edit command was terminated by signal "
                                 f"{-retcode}")
                else:
                    logger.info(f"Edit command returned: {retcode}")
            except OSError as error:
                logger.error(f"Edit command failed: {error}")
