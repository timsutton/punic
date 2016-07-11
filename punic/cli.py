__author__ = 'Jonathan Wight <jwight@mac.com>'

import shutil
import logging
import os

import click
from pathlib2 import Path

import punic
from punic.basic_types import *
from punic.utilities import *
from punic.model import *
from punic.runner import *
from punic.config import *

@click.group()
@click.option('--echo', default=False, is_flag=True, help="""Echo all commands to terminal.""")
@click.option('--verbose', default=False, is_flag=True, help="""Verbose logging.""")
# @click.option('--timing', default=False, is_flag=True) # TODO
@click.pass_context
def main(context, echo, verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format='%(message)s', level = level)
    runner.echo = echo
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.WARNING)
    requests_log.propagate = True
    punic = Punic()
    context.obj = punic


@main.command()
@click.pass_context
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
def resolve(context, fetch):
    """Resolve dependencies and output `Carthage.resolved` file.

    This subcommand does not build dependencies. Use this sub-command when a dependency has changed and you just want to update `Cartfile.resolved`.
    """
    with timeit('resolve'):
        logging.info("# Resolve")
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
        logging.info("# Update")
        platforms = parse_platforms(platform)

        if configuration:
            punic.config.configuration = configuration
        if platform:
            punic.config.platforms = parse_platforms(platform)
        punic.config.dump()


        punic.resolve(fetch = fetch)
        punic.build(dependencies = deps, fetch = fetch)


@main.command()
@click.pass_context
def checkout(context):
    """Checkout dependencies
    """
    with timeit('fetch'):
        logging.info("# Checkout")
        punic = context.obj
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
    with timeit('build'):
        logging.info("# Build")
        punic = context.obj

        if configuration:
            punic.config.configuration = configuration
        if platform:
            punic.config.platforms = parse_platforms(platform)
        punic.config.dump()

        punic.build(dependencies = deps, fetch = fetch)


@main.command()
@click.pass_context
@click.option('--configuration', default=None, help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma seperated list.""")
@click.argument('deps', nargs=-1)
def bootstrap(context, configuration, platform, deps):
    """Fetch & build dependencies
    """
    with timeit('bootstrap'):
        logging.info("# Bootstrap")
        punic = context.obj

        if configuration:
            punic.config.configuration = configuration
        if platform:
            punic.config.platforms = parse_platforms(platform)
        punic.config.dump()

        punic.fetch()
        punic.build(dependencies = deps, fetch = True)


@main.command()
@click.pass_context
@click.option('--configuration', default=None, help="""Dependency configurations to clean. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to clean. Comma seperated list.""")
@click.option('--xcode/--no-xcode', default=True, is_flag=True, help="""Clean xcode projects.""")
@click.option('--caches', default=False, is_flag=True, help="""Clean the global punic carthage files.""")
def clean(context, configuration, platform, xcode, caches):
    """Clean project & punic environment.
    """
    logging.info("# Clean")
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
        logging.info("# Graph")
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

@main.command()
@click.pass_context
def version(context):
    print punic.__version__

if __name__ == '__main__':
    import sys
    import os
    import shlex

    os.chdir('/Users/schwa/Desktop/3dr-Site-Scan-iOS')

    sys.argv = shlex.split('{} --verbose bootstrap'.format(sys.argv[0]))

    main()