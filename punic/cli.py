__author__ = 'Jonathan Wight <jwight@mac.com>'

import shutil
import logging

import click

from punic.basic_types import *
from punic.utilities import *
from punic.model import *
from punic.runner import *


@click.group()
@click.option('--echo', default=False, is_flag=True, help="""Echo all commands to terminal.""")
@click.option('--verbose', default=False, is_flag=True, help="""Verbose logging.""")
# @click.option('--timing', default=False, is_flag=True) # TODO
@click.pass_context
def main(context, echo, verbose):
    if context.obj:
        punic = context.obj
    else:
        punic = Punic()
        context.obj = punic

    logging.basicConfig(format='%(message)s', level= logging.DEBUG if verbose else logging.INFO)
    runner.echo = echo


@main.command()
@click.pass_context
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
def resolve(context, fetch):
    """Resolve dependencies and output `Carthage.resolved` file.

    This subcommand does not build dependencies. Use this sub-command when a dependency has changed and you just want to update `Cartfile.resolved`.
    """
    with timeit('resolve'):
        punic = context.obj
        punic.resolve(fetch = fetch)


@main.command()
@click.pass_context
@click.option('--configuration', default=None, help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma seperated list.""")
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.argument('deps', nargs=-1)
def update(context, configuration, platform, fetch, deps):
    """Resolve & build dependencies.

    """
    punic = context.obj
    with timeit('update'):
        platforms = parse_platforms(platform)
        punic.resolve(fetch = fetch)
        punic.build(configuration=configuration, platforms=platforms, dependencies = deps)


@main.command()
@click.pass_context
def checkout(context):
    """Checkout dependencies
    """
    punic = context.obj
    with timeit('fetch'):
        punic.fetch()


@main.command()
@click.pass_context
@click.option('--configuration', default=None, help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma seperated list.""")
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.argument('deps', nargs=-1)
def build(context, configuration, platform, fetch, deps):
    """Build dependencies
    """
    punic = context.obj
    with timeit('build'):
        platforms = parse_platforms(platform)
        punic.build(configuration=configuration, platforms=platforms, dependencies = deps, fetch = fetch)


@main.command()
@click.pass_context
@click.option('--configuration', default=None, help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma seperated list.""")
@click.argument('deps', nargs=-1)
def bootstrap(context, configuration, platform, deps):
    """Fetch & build dependencies
    """
    punic = context.obj
    with timeit('bootstrap'):
        platforms = parse_platforms(platform)
        punic.fetch()
        punic.build(configuration=configuration, platforms= platforms, dependencies = deps)


@main.command()
@click.pass_context
@click.option('--configuration', default=None, help="""Dependency configurations to clean. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to clean. Comma seperated list.""")
@click.option('--xcode/--no-xcode', default=True, is_flag=True, help="""Clean xcode projects.""")
@click.option('--caches', default=False, is_flag=True, help="""Clean the global punic carthage files.""")
def clean(context, configuration, platform, xcode, caches):
    """Clean project & punic environment.
    """
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
        runner.reset()


@main.command()
@click.pass_context
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
def graph(context, fetch):
    """Output resolved dependency graph"""
    with timeit('graph'):
        punic = context.obj
        graph = punic.graph(fetch = fetch)

        import networkx as nx

        logging.info('# Writing graph file to "{}".'.format(os.getcwd()))
        nx.drawing.nx_pydot.write_dot(graph, 'graph.dot')

        command = 'dot graph.dot -ograph.png -Tpng'
        if runner.can_run(command):
            logging.info('# Rendering dot file to png file.')
            runner.run(command)
        else:
            logging.warning('# graphviz not installed. Cannot convert graph to a png.')

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

    sys.argv = shlex.split('{} --verbose resolve --no-fetch'.format(sys.argv[0]))

    punic = Punic()

    main(obj=punic)