__author__ = 'schwa'
__all__ = ['Cartfile']

import re

from pathlib2 import Path
from utilities import Specification

class Cartfile(object):
    def __init__(self, specifications = None):
        self.specifications = specifications if specifications else []

    def read(self, input):
        if isinstance(input, Path):
            input = input.open().read()
        lines = [line.rstrip() for line in input.splitlines()]
        self.specifications = [Specification.cartfile_string(line) for line in lines if re.match(r'^github .+', str(line))]

    def write(self, output):
        strings = [str(specification) for specification in self.specifications]
        string = u'\n'.join(sorted(strings)) + '\n'
        output.write(string)

