
import logging

import punic.styling

class Logger(object):
    def __init__(self):
        pass

    def log(self, level, msg):
        msg = punic.styling.styled('<echo>#</echo> {}'.format(msg))
        logging.log(level, msg)

    def verbose(self, msg):
        self.log(logging.DEBUG, msg)

    def debug(self, msg):
        self.log(logging.DEBUG, msg)

    def info(self, msg):
        self.log(logging.INFO, msg)

    def error(self, msg):
        self.log(logging.ERROR, msg)

    def echo(self, msg):
        msg = punic.styling.styled('<echo>{}</echo>'.format(msg))
        logging.log(logging.DEBUG, msg)

logger = Logger()