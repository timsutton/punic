from __future__ import division, absolute_import, print_function

__all__ = ['Cartfile']

import re

from pathlib2 import Path

from .basic_types import *
from .errors import *


class Cartfile(object):
    def __init__(self, specifications=None, overrides=None):
        self.specifications = specifications if specifications else []
        self.overrides = overrides

    def read(self, source):
        # type: (Path)

        if isinstance(source, Path):
            if not source.exists():
                raise CartfileNotFound(path=source)
            source = source.open().read()
        lines = [line.rstrip() for line in source.splitlines()]
        self.specifications = [Specification.cartfile_string(line, self.overrides) for line in lines if
            re.match(r'^github .+', str(line))]

    def write(self, destination):
        # type: (File)
        strings = [str(specification) for specification in self.specifications]
        string = u'\n'.join(sorted(strings)) + '\n'
        destination.write(string)
