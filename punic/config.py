from __future__ import division, absolute_import, print_function

__all__ = ['Config', 'config']

from pathlib2 import Path
import pureyaml
from .basic_types import *
from .logger import *


class Config(object):
    def __init__(self):
        self.defaults = {
            'configuration': None,
            'platforms': [],
        }
        self.xcode = None
        self.repo_overrides = dict()

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

        if 'repo-overrides' in d:
            self.repo_overrides = d['repo-overrides']

    def dump(self):
        logger.info('Config:')
        logger.info('\tDefaults')
        for k, v in self.defaults.items():
            logger.info('\t\t{}: {}'.format(k, v))
        logger.info('\tOverrides: {}'.format(self.repo_overrides))

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
