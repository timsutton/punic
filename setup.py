#!/usr/bin/env python

from setuptools import setup

setup(
    name='punic',
    version='0.0.1',
    url='http://github.com/schwa/punic',
    license='MIT',
    author='Jonathan Wight',
    author_email='jwight@mac.com',
    description='Clean room python implementation of a subset of Carthage functionality',
    packages=['punic'],
    install_requires=[
        'click',
        'pathlib2',
        'networkx',
        'pygit2',
        'flufl.enum',
        'memoize',
        'blessings',
        ],
    entry_points='''
        [console_scripts]
        punic=punic.cli:main
        ''',
)
