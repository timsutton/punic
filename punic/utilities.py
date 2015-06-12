__author__ = 'schwa'
__all__ = ["SemanticVersion", "cwd"]

import re
import contextlib
import os

# TODO: Doesn't support full semvar.org spec
class SemanticVersion():
    def __init__(self, s):
        self.raw = s
        match = re.match("(?:v)?(\d+)(?:\.(\d+)(?:\.(\d+))?)?", s)
        if not match:
            raise Exception("\"{}\" not a semantic version.".format(s))
        groups = match.groups()
        self.major = int(groups[0])
        self.minor = int(groups[1]) if groups[1] else 0
        self.revision = int(groups[2]) if groups[2] else 0
    @property
    def value(self):
        return self.major * 100000 + self.minor * 1000 + self.revision
    @property
    def components(self):
        return (self.major, self.minor, self.revision)
    def __repr__(self):
        return "{}.{}.{}".format(*self.components)
    def __cmp__(self, other):
        return cmp(self.value, other.value)

@contextlib.contextmanager
def cwd(path):
    saved_wd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(saved_wd)
