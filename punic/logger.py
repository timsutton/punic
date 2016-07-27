from __future__ import division, absolute_import, print_function

__all__ = ['Logger', 'logger', 'HTMLFormatter', 'HTMLStripperFormatter']

import logging
import punic.styling
import six


# TODO: Convert < and > to &lt; and &gt;

class HTMLFormatter(object):
    def format(self, record):
        message = record.msg
        if not isinstance(message, six.string_types):
            message = repr(message)
        else:
            message = punic.styling.styled(message, True)
        return message


class HTMLStripperFormatter(object):
    def __init__(self, formatter=None):
        self.formatter = formatter

    def format(self, record):

        if self.formatter:
            message = self.formatter.format(record)
        else:
            message = record.msg
        if not isinstance(message, six.string_types):
            message = repr(message)
        else:
            message = punic.styling.styled(message, False)
        return message


# TODO: Deprecate
class Logger(object):
    def __init__(self):
        self.color = True

    def log(self, level, msg, prefix=True):
        # if not isinstance(msg, six.string_types):
        #     msg = repr(msg)
        # if prefix:
        #     msg = u'<echo>#</echo> ' + msg
        # msg = punic.styling.styled(msg, styled=self.color)
        logging.log(level, msg)

    def verbose(self, msg, prefix=True):
        self.log(logging.DEBUG, msg, prefix=prefix)

    def debug(self, msg, prefix=True):
        self.log(logging.DEBUG, msg, prefix=prefix)

    def info(self, msg, prefix=True):
        self.log(logging.INFO, msg, prefix=prefix)

    def warn(self, msg, prefix=True):
        self.log(logging.WARN, msg, prefix=prefix)

    def error(self, msg, prefix=True):
        self.log(logging.ERROR, msg, prefix=prefix)

    def echo(self, msg):
        msg = punic.styling.styled('<echo>{}</echo>'.format(msg), styled=self.color)
        self.info(msg, prefix=False)


logger = Logger()
