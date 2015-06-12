from distutils.core import setup

setup(
    name='punic',
    version='0.0.1',
    url='',
    license='MIT',
    author='Jonathan Wight',
    author_email='jwight@mac.com',
    description='Clean room python implementation of a subset of Carthage functionality',
    packages=['punic'],
    install_requires=['click', 'Pathlib', 'pygit2'],
    entry_points='''
        [console_scripts]
        punic=punic.cli:main
        ''',
)