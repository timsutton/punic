__author__ = 'schwa'

import shutil
import logging

import click

from punic.types import *
from punic.utilities import *
from punic.model import *


@click.group()
@click.option('--echo', default=False, is_flag=True)
@click.option('--verbose', default=False, is_flag=True)
@click.pass_context
def main(context, echo, verbose):
    if context.obj:
        punic = context.obj
    else:
        punic = Punic()
        context.obj = punic

    logging.basicConfig(format='%(message)s', level= logging.DEBUG if verbose else logging.INFO)
    punic.echo = echo


@main.command()
@click.pass_context
def resolve(context):
    punic = context.obj
    punic.resolve()


@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
@click.pass_context
def update(context, configuration, platform):
    punic = context.obj
    with timeit('update'):
        platforms = parse_platforms(platform)
        punic.resolve()
        punic.build(configuration=configuration, platforms=platforms)


@main.command()
@click.pass_context
def checkout(context):
    punic = context.obj
    with timeit('fetch'):
        punic.fetch()


@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
@click.pass_context
def build(context, configuration, platform):
    punic = context.obj
    with timeit('build'):
        platforms = parse_platforms(platform)
        punic.build(configuration=configuration, platforms=platforms)


@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
@click.pass_context
def bootstrap(context, configuration, platform):
    punic = context.obj
    with timeit('bootstrap'):
        platforms = parse_platforms(platform)
        punic.fetch()
        punic.build(configuration=configuration, platforms= platforms)


@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
@click.option('--xcode/--no-xcode', default=True, is_flag=True)
@click.option('--caches', default=False, is_flag=True)
@click.pass_context
def clean(context, configuration, platform, xcode, caches):
    punic = context.obj
    if xcode:
        logging.info('# Cleaning Xcode projects'.format(**punic.__dict__))
        platforms = parse_platforms(platform)
        punic.clean(configuration=configuration, platforms= platforms)

    if caches:
        if punic.repo_cache_directory.exists():
            logging.info('# Cleaning {repo_cache_directory}'.format(**punic.__dict__))
            shutil.rmtree(str(punic.repo_cache_directory))
        logging.info('# Cleaning run cache')
        punic.runner.reset()

# archive
# copy-frameworks
# outdated
# version

def parse_platforms(s):
    if not s:
        return Platform.all
    else:
        return [Platform.platform_for_nickname(platform.strip()) for platform in s.split(',')]


if __name__ == '__main__':
    import sys
    import os
    import shlex

    os.chdir('/Users/schwa/Desktop/3dr-Site-Scan-iOS')

    # sys.argv = shlex.split('{} --verbose --echo clean'.format(sys.argv[0]))
    # sys.argv = shlex.split('{} --verbose --echo build --platform=iOS --configuration=Debug'.format(sys.argv[0]))
    sys.argv = shlex.split('{} --verbose --echo build --platform=iOS --configuration=Debug'.format(sys.argv[0]))

    punic = Punic()

    main(obj=punic)