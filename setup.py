#!/usr/bin/env python

from setuptools import setup

setup(
    name='punic',
    version='0.1.2',
    url='http://github.com/schwa/punic',
    license='MIT',
    author='Jonathan Wight',
    author_email='jwight@mac.com',
    description='Clean room python implementation of a subset of Carthage functionality',
    packages=['punic'],
    install_requires=[
        'affirm',
        'blessings',
        'boto',
        'click',
        'click_didyoumean',
        'flufl.enum',
        'memoize',
        'networkx',
        'pathlib2',
        'prompt_toolkit',
        'pureyaml',
        'requests',
        'six',
        'tqdm',
        ],
    entry_points='''
        [console_scripts]
        punic=punic.punic_cli:main
        ''',
)
