import shutil
from pathlib2 import Path


def rmtree(path, ignore_errors=False, onerror=None):
    shutil.rmtree(str(path), ignore_errors, onerror)


def copytree(src, dst, symlinks=False, ignore=None):
    shutil.copytree(str(src), str(dst), symlinks, ignore)


def copy(src, dst):
    shutil.copy(str(src), str(dst))


def copyfile(src, dst):
    shutil.copyfile(str(src), str(dst))


def ignore_patterns(*patterns):
    return shutil.ignore_patterns(*patterns)


def move(src, dst):
    shutil.move(str(src), str(dst))
