__author__ = 'Jonathan Wight <jwight@mac.com>'
__all__ = ['Cartfile', 'Config', 'config']

import re

from pathlib2 import Path
import pureyaml

from punic.basic_types import *
from punic.logger import *

class Cartfile(object):
    def __init__(self, specifications=None):
        self.specifications = specifications if specifications else []

    def read(self, source):
        # type: (Path)

        if isinstance(source, Path):
            source = source.open().read()
        lines = [line.rstrip() for line in source.splitlines()]
        self.specifications = [Specification.cartfile_string(line) for line in lines if
                               re.match(r'^github .+', str(line))]

    def write(self, destination):
        # type: (File)
        strings = [str(specification) for specification in self.specifications]
        string = u'\n'.join(sorted(strings)) + '\n'
        destination.write(string)


class Config(object):
    def __init__(self):
        self.defaults = {
            'configuration': None,
            'platforms': [],
        }
        self.color = False

        self.read(Path('punic.yaml'))


    def read(self, path):
        # type: (Path)

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
        logger.echo('Config:')
        for k, v in self.defaults.items():
            logger.echo('\t{}: {}'.format(k, v))

    def update(self, configuration=None, platform=None):
        # type: (str, string) -> bool
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

config = Config()