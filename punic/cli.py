__author__ = 'schwa'

import click
from pathlib import Path
from punic import *


@click.group()
def main():
    pass

@main.command()
@click.option("--configuration", type=unicode, default=None, help="the Xcode configuration to build (ignored if --no-build option is present)")
@click.option("--platform", type=unicode, default="all", help="the platform (iOS or Mac) to build for (ignored if --no-build option is present)")
@click.option("--no-build", is_flag=True, help="skip the building of dependencies after updating")
@click.argument('only_dependencies', nargs=-1)
def update(configuration, platform, no_build, only_dependencies):
    punic = Punic(Path.cwd())
    punic.update()
    punic.resolve()
    if platform == "all":
        platform = None
    if no_build == False:
        punic.build(configuration = configuration, platform = platform, only_dependencies=only_dependencies)

@main.command()
@click.option("--configuration", type=unicode, default=None, help="the Xcode configuration to build (ignored if --no-build option is present)")
@click.option("--platform", type=unicode, default="all", help="the platform (iOS or Mac) to build for (ignored if --no-build option is present)")
@click.argument('only_dependencies', nargs=-1)
def bootstrap(configuration, platform, only_dependencies):
    punic = Punic(Path.cwd())
    punic.update()
    if platform == "all":
        platform = None
    punic.build(configuration = configuration, platform = platform, only_dependencies=only_dependencies)

if __name__ == '__main__':
    import sys
    import os
    sys.argv += ["update", "--platform=iOS"]
    os.chdir("/Users/schwa/Documents/Personal/Work/3DRobotics/Source/iSolo")
    main()