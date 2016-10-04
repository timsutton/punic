#!/usr/bin/env python

from setuptools import setup

def check_libyaml():
    import subprocess
    if not subprocess.check_output(['brew', 'ls', '--versions', 'libyaml']):
        import sys
        sys.stderr.write('Error: {}\nError: libyaml not installed. Use `brew install libyaml` to install it\nError: {}\n'.format('*' * 80, '*' * 80))
        exit(-1)

check_libyaml()


setup(
    name='punic',
    version='0.2.2',
    url='http://github.com/schwa/punic',
    license='MIT',
    author='Jonathan Wight',
    author_email='jwight@mac.com',
    description='Clean room python implementation of a subset of Carthage functionality',
    packages=['punic'],
    keywords = ['carthage', 'build', 'xcode', 'iOS', 'cocoapods', 'cocoa', 'macOS'],
    platform = "MacOS X",
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: MacOS X',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Build Tools',
        ],
    install_requires=[
        'affirm',
        'blessings',
        'boto',
        'click',
        'click_didyoumean',
        'flufl.enum',
        'jsonpath_rw',
        'memoize',
        'networkx',
        'pathlib2',
        'prompt_toolkit',
        'pyyaml',
        'requests',
        'six',
        'tqdm',
        ],
    entry_points='''
        [console_scripts]
        punic=punic.punic_cli:main
        ''',
)
