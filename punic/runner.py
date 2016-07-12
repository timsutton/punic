__author__ = 'Jonathan Wight <jwight@mac.com>'
__all__ = ['Runner', 'runner', 'Result']

import os
import subprocess
import logging
import shlex
import shelve

from memoize import mproperty

from punic.utilities import *


class Result(object):
    pass


class Runner(object):


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

    def result(self, command):
        result = self.run2(command)
        return result.return_code

    def run_(self, command, cwd=None, echo=None):
        try:
            if not cwd:
                cwd = os.getcwd()
            with work_directory(cwd):
                command = self.convert_args(command)

                real_echo = self.echo
                if echo != None:
                    real_echo = echo

                if real_echo:
                    logging.info(' '.join(command))
                return subprocess.check_output(command, stderr = subprocess.STDOUT)

        except subprocess.CalledProcessError, e:
            print e.output
            raise e

    def convert_args(self, args):
        if isinstance(args, basestring):
            args = shlex.split(args)
        else:
            args = [str(args) for args in args]
        return args

    def can_run(self, args):
        args = self.convert_args(args)
        popen = subprocess.Popen(['/usr/bin/env', 'which', args[0]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return_code = popen.wait()
        return True if return_code == 0 else False

    def run2(self, command):
        args = self.convert_args(command)
        popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return_code = popen.wait()


        result = Result()
        result.return_code = return_code
        result.stdout = popen.stdout
        result.stderr = popen.stderr
        return result

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

runner = Runner()