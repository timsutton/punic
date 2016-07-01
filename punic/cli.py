__author__ = 'schwa'

import click
from pathlib2 import Path

from punic.utilities import *
from punic.model import *
import shutil
import logging

punic = Punic()

@click.group()
@click.option('--echo', default=False, is_flag=True)
@click.option('--verbose', default=False, is_flag=True)
def main(echo, verbose):
    punic.echo = echo
    logging.basicConfig(format='%(message)s', level= logging.DEBUG if verbose else logging.INFO)


@main.command()
def resolve():
    punic.resolve()

@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
def update(configuration, platform):
    with timeit('update'):
        platforms = [Platform.platform_for_nickname(platform)]
        punic.resolve()
        punic.build(configuration=configuration, platforms=platforms)

@main.command()
def fetch():
    with timeit('fetch'):
        punic.fetch()


@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
def build(configuration, platform):
    with timeit('build'):
        platforms = [Platform.platform_for_nickname(platform)]
        punic.build(configuration=configuration, platforms=platforms)


@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
def bootstrap(configuration, platform):
    with timeit('bootstrap'):
        platforms = [Platform.platform_for_nickname(platform)]
        punic.fetch()
        punic.build(configuration=configuration, platforms= platforms)



@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
@click.option('--xcode/--no-xcode', default=True, is_flag=True)
@click.option('--caches', default=False, is_flag=True)
def clean(configuration, platform, xcode, caches):
    if xcode:
        logging.debug('# Cleaning Xcode projects'.format(**punic.__dict__))
        if not platform:
            platforms = Platform.all
        else:
            platforms = [Platform.platform_for_nickname(platform)]
        punic.clean(configuration=configuration, platforms= platforms)

    if caches:
        if punic.repo_cache_directory.exists():
            logging.debug('# Cleaning {repo_cache_directory}'.format(**punic.__dict__))
            shutil.rmtree(str(punic.repo_cache_directory))
        punic.cacheable_runner.reset()


if __name__ == '__main__':
    import sys
    import os
    import shlex

    os.chdir('/Users/schwa/Projects/3dr-Site-Scan-iOS')


#    sys.argv += ['build', '--configuration=Debug', '--platform=iOS']
#    sys.argv += ['resolve']
#    sys.argv += ['resolve']
    sys.argv = shlex.split('{} --verbose clean'.format(sys.argv[0]))
#    sys.argv += ['fetch']
    main()

