from __future__ import division, absolute_import, print_function

__all__ = ['carthage_cli']

import logging
import sys

import click

import punic
from .copy_frameworks import *
from .errors import *
from .logger import *
from .model import *
from .runner import *
from .semantic_version import *
from .utilities import *
from .version_check import *

@click.group()
@click.option('--echo', default=False, is_flag=True, help="""Echo all commands to terminal.""")
@click.option('--verbose', default=False, is_flag=True, help="""Verbose logging.""")
@click.option('--color/--no-color', default=True, is_flag=True, help="""TECHNICOLOR.""")
# @click.option('--timing', default=False, is_flag=True) # TODO
@click.pass_context
def carthage_cli(context, echo, verbose, color):
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


@carthage_cli.command()
@click.pass_context
def checkout(context):
    """Clones or fetches a Git repository ahead of time."""
    with timeit('fetch'):
        with error_handling():
            logger.info("<cmd>Checkout</cmd>")
            punic = context.obj
            punic.can_fetch = True # obviously
            punic.fetch()


@carthage_cli.command()
@click.pass_context
@click.option('--configuration', default=None,
    help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.argument('deps', nargs=-1)
def build(context, configuration, platform, deps):
    """Build the project's dependencies."""
    with timeit('build'):
        with error_handling():
            logger.info("<cmd>Build</cmd>")
            punic = context.obj
            punic.config.update(configuration=configuration, platform=platform)

            punic.can_fetch = False
            punic.build(dependencies=deps)


@carthage_cli.command()
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

            punic.can_fetch = fetch
            punic.resolve()
            punic.build(dependencies=deps)




@carthage_cli.command()
@click.pass_context
@click.option('--configuration', default=None,
    help="""Dependency configurations to build. Usually 'Release' or 'Debug'.""")
@click.option('--platform', default=None, help="""Platform to build. Comma separated list.""")
@click.argument('deps', nargs=-1)
def bootstrap(context, configuration, platform, deps):
    """Check out and build the project's dependencies."""
    with timeit('bootstrap'):
        with error_handling():
            logger.info("<cmd>Bootstrap</cmd>")
            punic = context.obj
            punic.can_fetch = True
            punic.config.update(configuration=configuration, platform=platform)
            punic.fetch()
            punic.build(dependencies=deps)


@carthage_cli.command(name = 'copy-frameworks')
@click.pass_context
def copy_frameworks(context):
    """In a Run Script build phase, copies each framework specified by a SCRIPT_INPUT_FILE environment variable into the built app bundle."""
    copy_frameworks_main()


# noinspection PyUnusedLocal
@carthage_cli.command()
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


