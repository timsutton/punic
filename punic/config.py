from __future__ import division, absolute_import, print_function

__all__ = ['Config', 'config']

import os
from pathlib2 import Path
import pureyaml
from .basic_types import *
from .logger import *
from .runner import *
from .xcode import *

class Config(object):
    def __init__(self):
        self.defaults = {
            'configuration': None,
            'platforms': [],
        }
        self.xcode = None
        self.repo_overrides = dict()

        self.root_path = Path.cwd()  # type: Path

        self.library_directory = Path(os.path.expanduser('~/Library/io.schwa.Punic'))
        if not self.library_directory.exists():
            self.library_directory.mkdir(parents=True)
        self.repo_cache_directory = self.library_directory / 'repo_cache'
        if not self.repo_cache_directory.exists():
            self.repo_cache_directory.mkdir(parents=True)
        self.punic_path = self.root_path / 'Carthage'
        self.build_path = self.punic_path / 'Build'
        self.checkouts_path = self.punic_path / 'Checkouts'

        self.derived_data_path = self.library_directory / "DerivedData"

        runner.cache_path = self.library_directory / "cache.shelf"

        self.can_fetch = False


        self.read(Path('punic.yaml'))
        self.xcode = None


    @property
    def xcode_version(self):
        return self.xcode.version if self.xcode else None

    @xcode_version.setter
    def xcode_version(self, value):
        self.xcode = Xcode.with_version(value)




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
