__author__ = 'schwa'
__all__ = ['run', 'CacheableRunner']

import os
import subprocess
import logging
import shlex
import shelve

from memoize import mproperty

from punic.utilities import *

def run(command, cwd=None, echo=True):
    try:
        if not cwd:
            cwd = os.getcwd()
        with work_directory(cwd):
            if isinstance(command, basestring):
                command = shlex.split(command)
            if echo:
                command = [str(command) for command in command]
                logging.info(' '.join(command))
            return subprocess.check_output(command)

    except subprocess.CalledProcessError, e:
        # raise Exception("command failed: {}".format(command))
        raise e

class CacheableRunner(object):
    def __init__(self, path):
        self.path = path
        self.echo = False

    @mproperty
    def shelf(self):
        try:
            return shelve.open(str(self.path))
        except:
            if self.path.exists():
                self.path.unlink()
                shelve.open(str(self.path))
            else:
                raise

    def reset(self):
        if self.path.exists():
            self.shelf.close()
            self.path.unlink()
            # TODO: Reopen


    def run(self, *args, **kwargs):
        if 'cache_key' in kwargs and 'command' in kwargs:
            key = kwargs['cache_key']
            command = kwargs['command']

            if 'echo' in kwargs:
                del kwargs['echo']
            kwargs['echo'] = self.echo

            key = '{}{}'.format(key, command)
            if key in self.shelf:
                return self.shelf[key]
            else:
                del kwargs['cache_key']
                result = run(*args, **kwargs)
                self.shelf[key] = result
                return result
        else:
            return run(*args, **kwargs)

