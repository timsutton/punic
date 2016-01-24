# punic

## Description

A clean room reimplementation of the Carthage dependency manager.

## Installation

This is python project, so you'll want pip installed first. If you don't have pip installed you'll want to do that first.

```
$ easy_install --user pip
Searching for pip
Best match: pip 7.0.3
Processing pip-7.0.3-py2.7.egg
pip 7.0.3 is already the active version in easy-install.pth
Installing pip script to /Users/schwa/Library/Python/2.7/bin
Installing pip2.7 script to /Users/schwa/Library/Python/2.7/bin
Installing pip2 script to /Users/schwa/Library/Python/2.7/bin

Using /Users/schwa/Library/Python/2.7/lib/python/site-packages/pip-7.0.3-py2.7.egg
Processing dependencies for pip
Finished processing dependencies for pip
```

Make sure pip was installed properly

```
$ which pip
/Users/schwa/Library/Python/2.7/bin/pip
```

Now install punic (the --upgrade switch means pip will upgrade any older versions of punic)

```
$ pip install --user --upgrade git+https://github.com/schwa/punic.git
```

## Usage

See https://github.com/Carthage/Carthage for usage information

Punic supports Cartfile and Cartfile.resolved

It currently supports a limited subset of Carthage features including limited subsets of 'update' and 'bootstrap'.

## License

MIT



