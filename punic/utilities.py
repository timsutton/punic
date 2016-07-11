__author__ = 'Jonathan Wight <jwight@mac.com>'
__all__ = ['work_directory', 'timeit']

import contextlib
import os
import logging
import time
import re

@contextlib.contextmanager
def work_directory(path):
    path = str(path)
    saved_wd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(saved_wd)

@contextlib.contextmanager
def timeit(task=None):
    start = time.time()
    yield
    end = time.time()
    logging.debug('# {} {}'.format(task if task else '<unnamed task>', end - start))





