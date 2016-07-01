# punic

## Description

A clean room reimplementation of (_parts_ of) the Carthage dependency manager.

## Installation

Quick install (for [homebrew](http://brew.sh) users):

```shell
$ brew install libgit2
$ brew install python2.7 # optional if you'd rather sudo pip install
$ pip install --user --upgrade git+https://github.com/schwa/punic.git
```

## Usage

Punic currently supports a subset of Carthage functionality.

```
Usage: punic [OPTIONS] COMMAND [ARGS]...

Options:
  --echo
  --verbose
  --help     Show this message and exit.

Commands:
  bootstrap
  build
  checkout
  clean
  resolve
  update
```

See https://github.com/Carthage/Carthage for usage information

Punic supports Carthage `Cartfile` and `Cartfile.resolved` files.

## Unsupported Carthage Features

* `carthage archive`
* `carthage copy-frameworks`
* `carthage outdated`
* `carthage fetch`

Most command line switches, including but not limited to `--use-ssh` and `--use-submodule`. Also Punic does not support (either creating or using) pre-built binary archives.

Punic only supports "github" style dependency specifications and does not support the use of branch names in version specifications.

## Frequently Answer Questions

### Why rewrite Carthage?

Carthage has had some rather severe performance and stability issues that have made it very hard to reliably use in production. These issues have historically proven very hard for the maintainers of Carthage to address. Instead of contributing fixes to Carthage it was deemed quicker and easier to produce a new clean room implementation of the concepts pioneered by the Carthage developers

(TODO: Link to Carthage issues.)

### What about Swift Package Manager?

Swift Package Manager is currently in its very early days and it will be a while before SPM is ready to be used to ship software. Until then Carthage and Punic still serve an important role.

### Why not use Cocoapods?

No thank you.

### Why Python and not Swift?

TODO: ~7000 lines of swift in Carthage (excluding dependencies) vs ~1000 lines of Python in Punic.
TODO: bootstrap problems

## License

MIT
