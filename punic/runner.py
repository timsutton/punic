__author__ = 'schwa'
__all__ = ['CacheableRunner', 'runner']

import os
import subprocess
import logging
import shlex
import shelve

from memoize import mproperty

from punic.utilities import *


class CacheableRunner(object):
    def __init__(self, cache_path = None):
        self.cache_path = cache_path
        self.echo = False

    @mproperty
    def shelf(self):
        if not self.cache_path:
            return None
        try:
            return shelve.open(str(self.cache_path))
        except:
            if self.cache_path.exists():
                self.cache_path.unlink()
                shelve.open(str(self.cache_path))
            else:
                raise

    def reset(self):
        if self.cache_path.exists():
            self.shelf.close()
            self.cache_path.unlink()
            # TODO: Reopen


    def run_(self, command, cwd=None, echo=None):
        try:
            if not cwd:
                cwd = os.getcwd()
            with work_directory(cwd):
                if isinstance(command, basestring):
                    command = shlex.split(command)
                else:
                    command = [str(command) for command in command]

                real_echo = self.echo
                if echo != None:
                    real_echo = echo

                if real_echo:
                    logging.info(' '.join(command))
                return subprocess.check_output(command)

        except subprocess.CalledProcessError, e:
            # raise Exception("command failed: {}".format(command))
            raise e


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
                result = self.run_(*args, **kwargs)
                self.shelf[key] = result
                return result
        else:
            result = self.run_(*args, **kwargs)
            return result

runner = CacheableRunner()