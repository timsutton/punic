#!/usr/bin/env python

from setuptools import setup

setup(
    name='punic',
    version='0.0.9',
    url='http://github.com/schwa/punic',
    license='MIT',
    author='Jonathan Wight',
    author_email='jwight@mac.com',
    description='Clean room python implementation of a subset of Carthage functionality',
    packages=['punic'],
    install_requires=[
        'affirm',
        'blessings',
        'click',
        'click_didyoumean',
        'flufl.enum',
        'memoize',
        'networkx',
        'pathlib2',
        'pureyaml',
        'requests',
        'six',
        ],
    entry_points='''
        [console_scripts]
        punic=punic:main
        carthage_punic=punic:main
        ''',
)
