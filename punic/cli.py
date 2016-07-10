__author__ = 'schwa'

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
@click.argument('deps', nargs=-1)
def update(context, configuration, platform, deps):
    """Resolve & build dependencies.

    """
    punic = context.obj
    with timeit('update'):
        platforms = parse_platforms(platform)
        punic.resolve()
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
@click.argument('deps', nargs=-1)
def build(context, configuration, platform, deps):
    """Build dependencies
    """
    punic = context.obj
    with timeit('build'):
        platforms = parse_platforms(platform)
        punic.build(configuration=configuration, platforms=platforms, dependencies = deps)


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

        nx.drawing.nx_pydot.write_dot(graph, '/Users/schwa/Desktop/graph.dot')
        runner.run('dot /Users/schwa/Desktop/graph.dot -o/Users/schwa/Desktop/graph.png -Tpng')
        #runner.run('open /Users/schwa/Desktop/graph.png')

        # from fabulous import image
        # print image.Image('/Users/schwa/Desktop/graph.png')

        # import matplotlib.pyplot as plt
        # pos = nx.spring_layout(graph)
        # nx.draw_networkx_nodes(graph, pos, nodelist=graph, node_color='r', alpha=0.2)
        # nx.draw_networkx_edges(graph, pos, nodelist=graph, edge_color='k', alpha=0.2, arrows = False)
        # nx.draw_networkx_labels(graph, pos, font_size = 9)
        #
        # plt.savefig("/Users/schwa/Desktop/graph.png")
        # runner.run('open /Users/schwa/Desktop/graph.png')

        # from networkx.drawing.nx_pydot import write_dot
        # write_dot(graph,'/Users/schwa/Desktop/file.dot')

def parse_platforms(s):
    if not s:
        return Platform.all
    else:
        return [Platform.platform_for_nickname(platform.strip()) for platform in s.split(',')]

if __name__ == '__main__':
    import sys
    import os
    import shlex

    os.chdir('/Users/schwa/Projects/3dr-Site-Scan-iOS')

    # sys.argv = shlex.split('{} --verbose --echo clean'.format(sys.argv[0]))
    # sys.argv = shlex.split('{} --verbose --echo build --platform=iOS --configuration=Debug'.format(sys.argv[0]))
    sys.argv = shlex.split('{} --verbose --echo graph --no-fetch'.format(sys.argv[0]))

    punic = Punic()

    main(obj=punic)