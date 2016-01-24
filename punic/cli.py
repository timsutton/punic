__author__ = 'schwa'

import click
from pathlib2 import Path

from punic.utilities import *
from punic.model import *
import shutil
import verboselogs

@click.group()
def main():
    pass

@main.command()
def resolve():
    punic = Punic()
    punic.resolve()

@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
def build(configuration, platform):
    with timeit('build'):
        platforms = [Platform.platform_for_nickname(platform)]
        punic = Punic()
        punic.build(configuration=configuration, platforms=platforms)


@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
def bootstrap(configuration, platform):
    with timeit('build'):
        platforms = [Platform.platform_for_nickname(platform)]
        punic = Punic()
        punic.build(configuration=configuration, platforms= platforms)



@main.command()
@click.option('--configuration', default=None)
@click.option('--platform', default=None)
def clean(configuration, platform):
    if not platform:
        platforms = Platform.all
    else:
        platforms = [Platform.platform_for_nickname(platform)]
    punic = Punic()
    punic.clean(configuration=configuration, platforms= platforms)


@main.command()
def nuke():
    punic = Punic(Path.cwd())
    clean(configuration = None, platform = None)
    shutil.rmtree(str(punic.scratch_directory))

# import toml
# import yaml
#
# @main.command()
# def init():
#
#     d = {
#         'name': 'Example Name',
#         'platforms': ['iOS', 'tvOS'],
#         'default_configuration': 'Debug',
#         'requirements': [
#             'Xcode "7.3.1"'
#         ],
#         'dependencies': [
#             'github "foo/bar" ~> 0.1',
#         ],
#         'build_order': [
#             'github "foo/bar" "0.1"',
#         ]
#     }
#
#     yaml.dump(d, Path('/Users/schwa/Desktop/punic.yaml').open('wb'))

if __name__ == '__main__':
    import sys
    import os

    os.chdir('/Users/schwa/Projects/punic/Testing/3dr-Site-Scan-iOS')
    sys.argv += ['build', '--configuration=Debug', '--platform=iOS']
#    sys.argv += ['clean']
#    sys.argv += ['init']
    main()
