__author__ = 'Jonathan Wight <jwight@mac.com>'
__all__ = ['Runner', 'runner', 'Result']

import os
import subprocess
import logging
import shlex
import shelve

from memoize import mproperty

from punic.utilities import *
import StringIO

class Result(object):
    pass


class Runner(object):
    def __init__(self, cache_path=None):
        self.cache_path = cache_path
        self.echo = False

    @mproperty
    def shelf(self):
        if not self.cache_path:
            return None
        # noinspection PyBroadException
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

    def result(self, command):
        result = self.run(command)
        return result.return_code

    def convert_args(self, args):
        if isinstance(args, basestring):
            args = shlex.split(args)
        else:
            args = [str(args) for args in args]
        return args

    def can_run(self, args):
        args = self.convert_args(args)
        result  = self.run(['/usr/bin/env', 'which', args[0]], echo = False)
        return True if result.return_code == 0 else False

    def check_run(self, *args, **kwargs):
        kwargs['check'] = True
        result = self.run(*args, **kwargs)
        return result.stdout

    def run(self, command, cwd = None, echo = None, cache_key = None, check = False):
        args = self.convert_args(command)

        if echo == True or self.echo == True:
            # TODO: Wont properly reproduce command if command is a string
            logging.info(' '.join(args))

        if cache_key:
            key = '{}{}'.format(cache_key, ' '.join(command))
            if key in self.shelf:
                logging.debug('CACHE HIT: {}'.format(key))
                return_code, stdout, stderr = self.shelf[key]
                result = Result()
                result.return_code = return_code
                result.stdout = stdout
                result.stderr = stderr
                return result

        stdout = subprocess.PIPE
        stderr = subprocess.PIPE if not check else subprocess.STDOUT

        popen = subprocess.Popen(args, cwd = cwd, stdout=stdout, stderr=stderr)
        stdout, stderr = popen.communicate()
        return_code = popen.returncode

        if check and return_code != 0:
            # TODO
            raise Exception('OOPS')

        if cache_key:
            key = '{}{}'.format(cache_key, ' '.join(command))
            self.shelf[key] = return_code, stdout, stderr

        result = Result()
        result.return_code = return_code
        result.stdout = stdout
        result.stderr = stderr

        return result


runner = Runner()
