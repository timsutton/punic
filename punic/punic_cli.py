from __future__ import division, absolute_import, print_function

__all__ = ['punic_cli', 'main']

import logging
import logging.handlers
import punic.shshutil as shutil
from pathlib2 import Path
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
from .basic_types import *

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

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(HTMLFormatter())
    # add ch to logger
    logger.addHandler(stream_handler)

    logs_path = Path('~/Library/io.schwa.Punic/Application Support/Logs').expanduser()
    if not logs_path.exists():
        logs_path.mkdir(parents = True)

    log_path = logs_path / "punic.log"
    needs_rollover = log_path.exists()

    file_handler = logging.handlers.RotatingFileHandler(str(log_path), backupCount=4)
    if needs_rollover:
        file_handler.doRollover()
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(HTMLStripperFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")))
    logger.addHandler(file_handler)


    for name in ['boto', 'requests.packages.urllib3']:
        named_logger = logging.getLogger(name)
        named_logger.setLevel(logging.WARNING)
        named_logger.propagate = True


    logger.color = color
    runner.echo = echo


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
@click.option('--toolchain', default=None, help="""Xcode toolchain to use""")
@click.option('--dry-run', default=None, is_flag=True, help="""TODO""")
@click.argument('deps', nargs=-1)
def build(context, configuration, platform, fetch, xcode_version, toolchain, dry_run, deps):
    """Fetch and build the project's dependencies."""
    logger.info("<cmd>Build</cmd>")
    punic = context.obj

    punic.config.can_fetch = fetch

    if platform:
        punic.config.platforms = parse_platforms(platform)
    if configuration:
        punic.config.configuration = configuration
    if toolchain:
        punic.config.toolchain = toolchain
    if xcode_version:
        punic.config.xcode_version = xcode_version
    if dry_run:
        punic.config.dry_run = dry_run


    logger.debug('Platforms: {}'.format(punic.config.platforms))
    logger.debug('Configuration: {}'.format(punic.config.configuration))

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
@click.option('--toolchain', default=None, help="""Xcode toolchain to use""")
@click.argument('deps', nargs=-1)
def update(context, configuration, platform, fetch, xcode_version, toolchain, deps):
    """Update and rebuild the project's dependencies."""
    logger.info("<cmd>Update</cmd>")
    punic = context.obj
    if platform:
        punic.config.platforms = parse_platforms(platform)
    if configuration:
        punic.config.configuration = configuration
    punic.config.can_fetch = fetch
    if toolchain:
        punic.config.toolchain = toolchain
    if xcode_version:
        punic.config.xcode_version = xcode_version

    with timeit('update', log = punic.config.log_timings):
        with error_handling():
            punic.resolve()
            punic.build(dependencies=deps)


@punic_cli.command()
@click.pass_context
@click.option('--derived-data', default=False, is_flag=True, help="""Clean the punic derived data directory.""")
@click.option('--caches', default=False, is_flag=True, help="""Clean the global punic files.""")
@click.option('--build', default=False, is_flag=True, help="""Clean the locate Carthage/Build directorys.""")
@click.option('--all', default=False, is_flag=True, help="""Clean all.""")
def clean(context, derived_data, caches, build, all):
    """Clean project & punic environment."""
    logger.info("<cmd>Clean</cmd>")
    punic = context.obj

    if build or all:
        logger.info('Erasing Carthage/Build directory')
        if punic.config.build_path.exists():
            shutil.rmtree(punic.config.build_path)

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
    """Display the current version of Punic."""
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
    """Cache punic build artifacts to Amazon S3"""
    pass

@cache.command()
@click.pass_context
@click.option('--xcode-version', default=None, help="""Xcode version to use""")
def publish(context, xcode_version):
    """Generates and uploads the cache archive for the current Cartfile.resolved"""
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
    """Installs the cache archive for the current Cartfile.resolved"""
    logger.info("<cmd>Cache Publish</cmd>")
    punic = context.obj
    if xcode_version:
        punic.config.xcode_version = xcode_version

    carthage_cache = CarthageCache(config = punic.config)
    logger.info("Cache filename: <ref>'{}'</ref>".format(carthage_cache.archive_name_for_project()))
    carthage_cache.install()


def main():
    punic_cli()
