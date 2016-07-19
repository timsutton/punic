from __future__ import division, absolute_import, print_function

__all__ = ['Logger', 'logger']

import logging
import punic.styling


class Logger(object):
    def __init__(self):
        self.color = True

    def log(self, level, msg, prefix = True):
        if prefix:
            msg = u'<echo>#</echo> ' + unicode(msg, encoding = 'utf-8')
        msg = punic.styling.styled(msg, styled=self.color)
        logging.log(level, msg)

    def verbose(self, msg, prefix = True):
        self.log(logging.DEBUG, msg, prefix = prefix)

    def debug(self, msg, prefix = True):
        self.log(logging.DEBUG, msg, prefix = prefix)

    def info(self, msg, prefix = True):
        self.log(logging.INFO, msg, prefix = prefix)

    def warn(self, msg, prefix = True):
        self.log(logging.WARN, msg, prefix = prefix)

    def error(self, msg, prefix = True):
        self.log(logging.ERROR, msg, prefix = prefix)

    def echo(self, msg):
        msg = punic.styling.styled('<echo>{}</echo>'.format(msg), styled=self.color)
        self.info(msg, prefix = False)


logger = Logger()
