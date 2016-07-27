from __future__ import division, absolute_import, print_function

__all__ = ['Config', 'config']

import os
from pathlib2 import Path
import yaml
from .basic_types import *
from .logger import *
from .runner import *
from .xcode import *

# TODO: This all needs to be cleaned up and made more generic. More configs will be added over time and this will only get worse
# TODO: Allow config file to be relocated and specified on command line
# TODO: Allow subcommands to easily override configs

class Config(object):
    def __init__(self):
        self.xcode = None
        self.repo_overrides = dict()

        self.root_path = Path.cwd()  # type: Path

        self.library_directory = Path('~/Library/Application Support/io.schwa.Punic').expanduser()
        if not self.library_directory.exists():
            self.library_directory.mkdir(parents=True)
        self.repo_cache_directory = self.library_directory / 'repo_cache'
        if not self.repo_cache_directory.exists():
            self.repo_cache_directory.mkdir(parents=True)
        self.punic_path = self.root_path / 'Carthage'
        self.build_path = self.punic_path / 'Build'
        self.checkouts_path = self.punic_path / 'Checkouts'

        self.derived_data_path = self.library_directory / "DerivedData"

        self.platforms = Platform.all
        self.configuration = None

        self.can_fetch = False
        self.xcode = Xcode.default()

        self.toolchain = None
        self.dry_run = False

        # Read in defaults from punic.yaml
        self.read(Path('punic.yaml'))

        runner.cache_path = self.library_directory / "cache.shelf"

    @property
    def xcode_version(self):
        return self.xcode.version if self.xcode else None

    @xcode_version.setter
    def xcode_version(self, value):
        xcode = Xcode.with_version(value)
        if value and not xcode:
            raise Exception('Could not find xcode version: {}'.format(value))
        if not xcode:
            xcode = Xcode.default()
        self.xcode = xcode


    def read(self, path):
        # type: (Path)

        if not path.exists():
            return

        d = yaml.safe_load(path.open())
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

        if 'xcode-version' in d:
            xcode_version = d['xcode-version']
            self.xcode_version = xcode_version

    def dump(self):
        logger.info('Config:')
        logger.info('\tDefaults')
        for k, v in self.defaults.items():
            logger.info('\t\t{}: {}'.format(k, v))
        logger.info('\tOverrides: {}'.format(self.repo_overrides))


config = Config()
