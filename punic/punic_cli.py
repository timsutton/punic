from __future__ import division, absolute_import, print_function

__all__ = ['punic_cli', 'main']

import logging
import punic.shshutil as shutil
import sys
import click
from click_didyoumean import DYMGroup
import networkx as nx
import punic
from .copy_frameworks import *
from .errors import *
from .logger import *
from .model import *
from .runner import *
from .semantic_version import *
from .utilities import *
from .version_check import *
from .config_init import *
from .carthage_cache import *

@click.group(cls=DYMGroup)
@click.option('--echo', default=False, is_flag=True, help="""Echo all commands to terminal.""")
@click.option('--verbose', default=False, is_flag=True, help="""Verbose logging.""")
@click.option('--color/--no-color', default=True, is_flag=True, help="""TECHNICOLOR.""")
@click.option('--timing/--no-timing', default=False, is_flag=True, help="""Log timing info""")
@click.pass_context
def punic_cli(context, echo, verbose, timing, color):

    # Configure click
    context.token_normalize_func = lambda x:x if not x else x.lower()

    # Configure logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format='%(message)s', level=level)
    runner.echo = echo
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.WARNING)
    requests_log.propagate = True
    logger.color = color

    # Set up punic
    punic = Punic()
    punic.config.log_timings = timing
    context.obj = punic


@punic_cli.command()
@click.pass_context
def fetch(context):
    """Fetch the project's dependencies.."""
    logger.info("<cmd>fetch</cmd>")
    punic = context.obj
    punic.config.can_fetch = True  # obviously

    with timeit('fetch', log = punic.config.log_timings):
        with error_handling():
            punic.fetch()


@punic_cli.command()
@click.pass_context
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
def resolve(context, fetch):
    """Resolve dependencies and output `Carthage.resolved` file.

    This sub-command does not build dependencies. Use this sub-command when a dependency has changed and you just want to update `Cartfile.resolved`.
    """
    punic = context.obj
    logger.info("<cmd>Resolve</cmd>")
    punic.config.can_fetch = fetch

    with timeit('resolve', log = punic.config.log_timings):
        with error_handling():
            punic.resolve()


@punic_cli.command()
@click.pass_context
@click.option('--configuration', default=None,
    help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.option('--xcode-version', default=None, help="""Xcode version to use""")
@click.argument('deps', nargs=-1)
def build(context, configuration, platform, fetch, xcode_version, deps):
    """Fetch and build the project's dependencies."""
    logger.info("<cmd>Build</cmd>")
    punic = context.obj

    punic.config.update(configuration=configuration, platform=platform)
    punic.config.can_fetch = fetch
    if xcode_version:
        punic.config.xcode_version = xcode_version

    with timeit('build', log = punic.config.log_timings):
        with error_handling():
            punic.build(dependencies=deps)


@punic_cli.command()
@click.pass_context
@click.option('--configuration', default=None,
    help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.option('--xcode-version', default=None, help="""Xcode version to use""")
@click.argument('deps', nargs=-1)
def update(context, configuration, platform, fetch, xcode_version, deps):
    """Update and rebuild the project's dependencies."""
    logger.info("<cmd>Update</cmd>")
    punic = context.obj
    punic.config.update(configuration=configuration, platform=platform)
    punic.config.can_fetch = fetch
    if xcode_version:
        punic.config.xcode_version = xcode_version

    with timeit('update', log = punic.config.log_timings):
        with error_handling():
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
        logger.info('Erasing derived data directory')
        if punic.config.derived_data_path.exists():
            shutil.rmtree(punic.config.derived_data_path)

    if caches or all:
        if punic.config.repo_cache_directory.exists():
            logger.info('Erasing {}'.format(punic.config.repo_cache_directory))
            shutil.rmtree(punic.config.repo_cache_directory )
        logger.info('Erasing run cache')
        runner.reset()


@punic_cli.command()
@click.pass_context
@click.option('--fetch/--no-fetch', default=True, is_flag=True, help="""Controls whether to fetch dependencies.""")
@click.option('--open', default=False, is_flag=True, help="""Open the graph image file.""")
def graph(context, fetch, open):
    """Output resolved dependency graph."""
    logger.info("<cmd>Graph</cmd>")
    punic = context.obj
    punic.config.can_fetch = fetch

    with timeit('graph', log = punic.config.log_timings):
        with error_handling():

            graph = punic.graph()

            logger.info('Writing graph file to "{}".'.format(os.getcwd()))
            nx.drawing.nx_pydot.write_dot(graph, 'graph.dot')

            command = 'dot graph.dot -ograph.png -Tpng'
            if runner.can_run(command):
                logger.info('Rendering dot file to png file.')
                runner.check_run(command)
                if open:
                    click.launch('graph.png')
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

@punic_cli.command()
@click.pass_context
@click.option('--configuration', default=None, help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.option('--xcode', default=None)
def init(context, **kwargs):
    """Generate punic configuration file."""

    config_init(**kwargs)

@punic_cli.command()
@click.pass_context
def readme(context):
    """Opens punic readme in your browser (https://github.com/schwa/punic/blob/HEAD/README.markdown)"""
    click.launch('https://github.com/schwa/punic/blob/HEAD/README.markdown')



@punic_cli.group(cls=DYMGroup)
@click.pass_context
def cache(context):
    """TODO"""
    pass

@cache.command()
@click.pass_context
@click.option('--xcode-version', default=None, help="""Xcode version to use""")
def publish(context, xcode_version):
    """TODO"""
    logger.info("<cmd>Cache Publish</cmd>")
    punic = context.obj
    if xcode_version:
        punic.config.xcode_version = xcode_version
    carthage_cache = CarthageCache(config = punic.config)
    logger.info("Cache filename: <ref>'{}'</ref>".format(carthage_cache.archive_name_for_project()))
    carthage_cache.publish()

@cache.command()
@click.pass_context
@click.option('--xcode-version', default=None, help="""Xcode version to use""")
def install(context, xcode_version):
    """TODO"""
    logger.info("<cmd>Cache Publish</cmd>")
    punic = context.obj
    if xcode_version:
        punic.config.xcode_version = xcode_version

    carthage_cache = CarthageCache(config = punic.config)
    logger.info("Cache filename: <ref>'{}'</ref>".format(carthage_cache.archive_name_for_project()))
    carthage_cache.install()


def main():
    punic_cli()
