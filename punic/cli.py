__author__ = 'schwa'

import click
from pathlib2 import Path

from punic.utilities import *
from punic.model import *
import shutil
import logging

@click.group()
@click.option('--echo', default=False, is_flag=True)
def main(echo):
    pass

@main.command()
def resolve():
    punic = Punic()
    punic.resolve()

@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
def update(configuration, platform):
    with timeit('update'):
        platforms = [Platform.platform_for_nickname(platform)]
        punic = Punic()
        punic.resolve()
        punic.build(configuration=configuration, platforms=platforms)

@main.command()
def fetch():
    with timeit('fetch'):
        punic = Punic()
        punic.fetch()


@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
def build(configuration, platform):
    with timeit('build'):
        platforms = [Platform.platform_for_nickname(platform)]
        punic = Punic()
        punic.build(configuration=configuration, platforms=platforms)


@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
def bootstrap(configuration, platform):
    with timeit('bootstrap'):
        platforms = [Platform.platform_for_nickname(platform)]
        punic = Punic()
        punic.build(configuration=configuration, platforms= platforms)



@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
@click.option('--xcode/--no-xcode', default=True, is_flag=True)
@click.option('--caches', default=False, is_flag=True)
def clean(configuration, platform, xcode, caches):
    punic = Punic()
    if xcode:
        logging.info('# Cleaning Xcode projects'.format(**punic.__dict__))
        if not platform:
            platforms = Platform.all
        else:
            platforms = [Platform.platform_for_nickname(platform)]
        punic.clean(configuration=configuration, platforms= platforms)

    if caches:
        if punic.repo_cache_directory.exists():
            logging.info('# Cleaning {repo_cache_directory}'.format(**punic.__dict__))
            shutil.rmtree(str(punic.repo_cache_directory))
        punic.cacheable_runner.reset()

if __name__ == '__main__':
    import sys
    import os

    os.chdir('/Users/schwa/Projects/punic/Testing/3dr-Site-Scan-iOS')
#    sys.argv += ['build', '--configuration=Debug', '--platform=iOS']
#    sys.argv += ['clean', '--caches']
#    sys.argv += ['resolve']
#    sys.argv += ['bootstrap', '--configuration=Debug', '--platform=iOS']
    sys.argv += ['fetch']
    main()
