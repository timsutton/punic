from __future__ import division, absolute_import, print_function

__all__ = ['punic_cli', 'main']

import logging
import os
import punic.shshutil as shutil
import sys
import click
from click_didyoumean import DYMGroup
import punic
from .copy_frameworks import *
from .errors import *
from .logger import *
from .model import *
from .runner import *
from .semantic_version import *
from .utilities import *
from .version_check import *


@click.group(cls=DYMGroup)
@click.option('--echo', default=False, is_flag=True, help="""Echo all commands to terminal.""")
@click.option('--verbose', default=False, is_flag=True, help="""Verbose logging.""")
@click.option('--color/--no-color', default=True, is_flag=True, help="""TECHNICOLOR.""")
# @click.option('--timing', default=False, is_flag=True) # TODO
@click.pass_context
def punic_cli(context, echo, verbose, color):

    context.token_normalize_func = lambda x:x if not x else x.lower()

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format='%(message)s', level=level)
    runner.echo = echo
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.WARNING)
    requests_log.propagate = True

    logger.color = color

    punic = Punic()
    context.obj = punic

    # Dont do this here. use `punic version`
    # version_check()


@punic_cli.command()
@click.pass_context
def fetch(context):
    """Fetch the project's dependencies.."""
    with timeit('fetch'):
        with error_handling():
            logger.info("<cmd>fetch</cmd>")
            punic = context.obj
            punic.config.can_fetch = True # obviously

            punic.fetch()



@punic_cli.command()
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
            punic.config.can_fetch = fetch

            punic.resolve()


@punic_cli.command()
@click.pass_context
@click.option('--configuration', default=None,
    help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.argument('deps', nargs=-1)
def build(context, configuration, platform, fetch, deps):
    """Fetch and build the project's dependencies."""
    with timeit('build'):
        with error_handling():
            logger.info("<cmd>Build</cmd>")
            punic = context.obj
            punic.config.update(configuration=configuration, platform=platform)
            punic.config.can_fetch = fetch

            punic.build(dependencies=deps)


@punic_cli.command()
@click.pass_context
@click.option('--configuration', default=None,
    help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.argument('deps', nargs=-1)
def update(context, configuration, platform, fetch, deps):
    """Update and rebuild the project's dependencies."""
    with timeit('update'):
        with error_handling():
            logger.info("<cmd>Update</cmd>")
            punic = context.obj
            punic.config.update(configuration=configuration, platform=platform)
            punic.config.can_fetch = fetch

            punic.resolve()
            punic.build(dependencies=deps)



@punic_cli.command()
@click.pass_context
@click.option('--derived-data', default=False, is_flag=True, help="""Clean the punic derived data directory.""")
@click.option('--caches', default=False, is_flag=True, help="""Clean the global punic carthage files.""")
@click.option('--all', default=False, is_flag=True, help="""Clean all.""")
def clean(context, derived_data, caches, all):
    """Clean project & punic environment."""
    logger.info("<cmd>Clean</cmd>")
    punic = context.obj

    if derived_data or all:
        logger.info('Erasing derived data directory'.format(**punic.__dict__))
        if punic.config.derived_data_path.exists():
            shutil.rmtree(punic.config.derived_data_path)

    if caches or all:
        if punic.config.repo_cache_directory.exists():
            logger.info('Cleaning {}'.format(punic.config.repo_cache_directory))
            shutil.rmtree(punic.config.repo_cache_directory )
        logger.info('Cleaning run cache')
        runner.reset()


@punic_cli.command()
@click.pass_context
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.option('--open', default=False, is_flag=True, help="""Open the graph image file.""")
def graph(context, fetch, open):
    """Output resolved dependency graph."""
    with timeit('graph'):
        with error_handling():
            logger.info("<cmd>Graph</cmd>")
            punic = context.obj
            punic.config.can_fetch = fetch
            graph = punic.graph()

            import networkx as nx

            logger.info('Writing graph file to "{}".'.format(os.getcwd()))
            nx.drawing.nx_pydot.write_dot(graph, 'graph.dot')

            command = 'dot graph.dot -ograph.png -Tpng'
            if runner.can_run(command):
                logger.info('Rendering dot file to png file.')
                runner.check_run(command)
                if open:
                    runner.run('open graph.png')
            else:
                logging.warning('graphviz not installed. Cannot convert graph to a png.')


@punic_cli.command(name ='copy-frameworks')
@click.pass_context
def copy_frameworks(context):
    """In a Run Script build phase, copies each framework specified by a SCRIPT_INPUT_FILE environment variable into the built app bundle."""
    copy_frameworks_main()


# noinspection PyUnusedLocal
@punic_cli.command()
@click.pass_context
def version(context):
    """Display the current version of Carthage."""
    logger.info('Punic version: {}'.format(punic.__version__), prefix = False)

    sys_version = sys.version_info
    sys_version = SemanticVersion.from_dict(dict(
        major = sys_version.major,
        minor = sys_version.minor,
        micro = sys_version.micro,
        releaselevel = sys_version.releaselevel,
        serial = sys_version.serial,
    ))

    logger.info('Python version: {}'.format(sys_version), prefix=False)
    version_check(verbose = True, timeout = None, failure_is_an_option=False)

from .config_init import config_init

@punic_cli.command()
@click.pass_context
@click.option(
    '--configuration', default=None,
    help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option(
    '--platform', default=None,
    help="""Platform to build. Comma separated list.""")
@click.option(
    '--xcode', default=None)
def init(context, **kwargs):
    """Generate punic configuration file."""

    config_init(**kwargs)


def main():
    punic_cli()
