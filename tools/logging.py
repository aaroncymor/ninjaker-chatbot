# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import os
from datetime import datetime


class DateStampedHandler(logging.FileHandler):
    """
    TODO: From wyrlsutils project. Borrowing this so the app would not be dependent
    on the said project.

    A handler class which writes formatted logging records to disk files. The filename is interpolated with strftime.
    """
    def __init__(self, filename_template, mode='a', encoding=None):
        self.filename_template = filename_template
        self.__log_date = datetime.today()
        super(DateStampedHandler, self).__init__(self.get_log_path(), mode, encoding)
        self.close()

    def _open(self):
        """
        Open the current base file with the (original) mode and encoding. Create directories as necessary.
        Return the resulting stream.
        """
        log_path = self.get_log_path()
        log_dir_path = os.path.dirname(log_path)
        if not os.path.isdir(log_dir_path):
            # Create directories as necessary
            os.makedirs(log_dir_path)

        if self.encoding is None:
            stream = open(log_path, self.mode)
        else:
            stream = codecs.open(log_path, self.mode, self.encoding)
        return stream

    # noinspection PyMethodMayBeStatic
    def get_log_path(self):
        """
        Build path to log file, applying strftime() formatting to the filename template
        """
        today = datetime.now()
        log_path = today.strftime(self.filename_template)
        return log_path

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the file with a trailing newline.

        If exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.

        :param record: log record
        :type record: logging.LogRecord
        """
        curr_date = datetime.today()
        if self.__log_date is None or self.__log_date != curr_date:
            self.close()
            self.__log_date = curr_date

        logging.FileHandler.emit(self, record)

