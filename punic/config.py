__author__ = 'Jonathan Wight <jwight@mac.com>'
__all__ = ['Cartfile', 'Config']

import re
import logging

from pathlib2 import Path
import pureyaml

from punic.basic_types import *

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

class Config(object):
    def __init__(self):
        self.defaults = {
            'configuration': None,
            'platforms': [],
        }
        self.read(Path('punic.yaml'))

    def read(self, path):

        if not path.exists():
            return

        d = pureyaml.load(path.open())
        if 'defaults' in d:
            defaults = d['defaults']
            if 'configuration' in defaults:
                self.configuration = defaults['configuration']
            if 'platforms' in defaults:
                self.platforms = parse_platforms(defaults['platforms'])
            elif 'platform' in defaults:
                self.platforms = parse_platforms(defaults['platform'])

    def dump(self):
        logging.debug('# Config:')
        for k, v in self.defaults.items():
            logging.debug('# \t{}: {}'.format(k, v))

    def update(self, configuration = None, platform = None):
        if configuration:
            self.configuration = configuration
        if platform:
            self.platforms = parse_platforms(platform)

    @property
    def configuration(self):
        return self.defaults['configuration']

    @configuration.setter
    def configuration(self, configuration):
        self.defaults['configuration'] = configuration


    @property
    def platforms(self):
        return self.defaults['platforms']


    @platforms.setter
    def platforms(self, platforms):
        self.defaults['platforms'] = platforms

