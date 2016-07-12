__author__ = 'Jonathan Wight <jwight@mac.com>'

import shutil
import logging
import os
import contextlib

import click

import punic
from punic.basic_types import *
from punic.utilities import *
from punic.model import *
from punic.runner import *
from punic.errors import *
from punic.config import *
from punic.logger import *

@click.group()
@click.option('--echo', default=False, is_flag=True, help="""Echo all commands to terminal.""")
@click.option('--verbose', default=False, is_flag=True, help="""Verbose logging.""")
@click.option('--color/--no-color', default=True, is_flag=True, help="""TECHNICOLOR.""")
# @click.option('--timing', default=False, is_flag=True) # TODO
@click.pass_context
def main(context, echo, verbose, color):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format='%(message)s', level=level)
    runner.echo = echo
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.WARNING)
    requests_log.propagate = True

    config.color = color

    punic = Punic()
    context.obj = punic


@main.command()
@click.pass_context
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
def resolve(context, fetch):
    """Resolve dependencies and output `Carthage.resolved` file.

    This sub-command does not build dependencies. Use this sub-command when a dependency has changed and you just want to update `Cartfile.resolved`.
    """
    with timeit('resolve'):
        with error_handling():
            logger.info("<cmd>Resolve</cmd>")
            punic = context.obj
            punic.resolve(fetch=fetch)


@main.command()
@click.pass_context
@click.option('--configuration', default=None,
              help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.argument('deps', nargs=-1)
def update(context, configuration, platform, fetch, deps):
    """Resolve & build dependencies."""
    with timeit('update'):
        with error_handling():
            logger.info("<cmd>Update</cmd>")
            punic = context.obj
            punic.config.update(configuration=configuration, platform=platform)
            punic.resolve(fetch=fetch)
            punic.build(dependencies=deps, fetch=fetch)


@main.command()
@click.pass_context
def checkout(context):
    """Checkout dependencies."""
    with timeit('fetch'):
        with error_handling():
            logger.info("<cmd>Checkout</cmd>")
            punic = context.obj
            punic.fetch()


@main.command()
@click.pass_context
@click.option('--configuration', default=None,
              help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.argument('deps', nargs=-1)
def build(context, configuration, platform, fetch, deps):
    """Build dependencies."""
    with timeit('build'):
        with error_handling():
            logger.info("<cmd>Build</cmd>")
            punic = context.obj
            punic.config.update(configuration=configuration, platform=platform)
            punic.build(dependencies=deps, fetch=fetch)


@main.command()
@click.pass_context
@click.option('--configuration', default=None,
              help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.argument('deps', nargs=-1)
def bootstrap(context, configuration, platform, deps):
    """Fetch & build dependencies."""
    with timeit('bootstrap'):
        with error_handling():
            logger.info("<cmd>Bootstrap</cmd>")
            punic = context.obj
            punic.config.update(configuration=configuration, platform=platform)
            punic.fetch()
            punic.build(dependencies=deps, fetch=True)


@main.command()
@click.pass_context
@click.option('--configuration', default=None,
              help="""Dependency configurations to clean. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to clean. Comma separated list.""")
@click.option('--xcode/--no-xcode', default=True, is_flag=True, help="""Clean xcode projects.""")
@click.option('--caches', default=False, is_flag=True, help="""Clean the global punic carthage files.""")
def clean(context, configuration, platform, xcode, caches):
    """Clean project & punic environment."""
    logger.info("<cmd>Clean</cmd>")
    punic = context.obj
    if xcode:
        logger.info('Cleaning Xcode projects'.format(**punic.__dict__))
        platforms = parse_platforms(platform)
        punic.clean(configuration=configuration, platforms=platforms)

    if caches:
        if punic.repo_cache_directory.exists():
            logger.info('Cleaning {repo_cache_directory}'.format(**punic.__dict__))
            shutil.rmtree(str(punic.repo_cache_directory))
        logger.info('Cleaning run cache')
        runner.reset()


@main.command()
@click.pass_context
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
def graph(context, fetch):
    """Output resolved dependency graph"""
    with timeit('graph'):
        with error_handling():
            logger.info("<cmd>Graph</cmd>")
            punic = context.obj
            graph = punic.graph(fetch=fetch)

            import networkx as nx

            logger.info('Writing graph file to "{}".'.format(os.getcwd()))
            nx.drawing.nx_pydot.write_dot(graph, 'graph.dot')

            command = 'dot graph.dot -ograph.png -Tpng'
            if runner.can_run(command):
                logger.info('Rendering dot file to png file.')
                runner.check_run(command)
            else:
                logging.warning('graphviz not installed. Cannot convert graph to a png.')


# noinspection PyUnusedLocal
@main.command()
@click.pass_context
def version(context):
    """Print punic version"""
    print punic.__version__


@contextlib.contextmanager
def error_handling():
    try:
        yield
    except RepositoryNotClonedError:
        logger.error("# Error: No locally cloned repository found. Did you neglect to run `punic checkout` first?")
    except:
        raise
