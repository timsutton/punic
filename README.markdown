# punic

## Description

A clean room reimplementation of (_parts_ of) the Carthage dependency manager.

## Installation

Quick install (for [homebrew](http://brew.sh) users):

```shell
$ brew install python2.7 # optional - but generally easiest way to make a sane python setup if you're not a python expert
$ pip install --upgrade git+https://github.com/schwa/punic.git
```

*Update!*

Punic is now python 3 compatible too (tested on python 3.5).

```shell
$ brew install python3
$ pip3 install --upgrade git+https://github.com/schwa/punic.git
```

Note: testing primarily occurs with Python 2.7. So until punic gets continuous integration (and more unit tests) it might be safer to run Punic under Python 2.7. But go on; be daring and use Python 3.5!

## Usage

Punic currently supports a subset of Carthage functionality.

```shell
$ punic
Usage: punic [OPTIONS] COMMAND [ARGS]...

Options:
  --echo     Echo all commands to terminal.
  --verbose  Verbose logging.
  --help     Show this message and exit.

Commands:
  bootstrap  Fetch & build dependencies
  build      Build dependencies
  checkout   Checkout dependencies
  clean      Clean project & punic environment.
  graph      Output resolved dependency graph
  resolve    Resolve dependencies and output...
  update     Resolve & build dependencies.
  version    Print punic version
```

See https://github.com/Carthage/Carthage for usage information

Punic supports Carthage `Cartfile` and `Cartfile.resolved` files.

## Caveat!!!

Punic can be considered an early preview release and probably is not ready for production use. Use at your own peril.

## Differences between Punic & Carthage

Aside from differences of implementation one of the fundamental differences is that Carthage always runs `xcodebuild clean` before building dependencies. Punic deliberately does not perform this clean step and provides an explicit `punic clean` command. The goal of this is to not force collaborators to sit through long clean builds when very little has changed. This can provide dramatic speed ups to a users workflow (during testing builds that can take Carthage 20-25 minutes to build on top-end hardware take less than a minute to do a 'dirty' build.)

Punic only supports "github" style dependency specifications and does not support the use of branch names in version specifications.

A complete list of Carthage compatibility as of version 0.16.2 of Carthage follows:

| Command/Switch                  | Status                             |
| ---------------                 | ---------------------------------- |
| archive                         | Won't implement. Note 1            |
| bootstrap                       | Implemented                        |
| bootstrap / --configuration     | Implemented                        |
| bootstrap / --platform          | Implemented                        |
| bootstrap / --derived-data      | _Unimplemented_                    |
| bootstrap / --verbose           | Implemented                        |
| bootstrap / --no-checkout       | _Unimplemented_                    |
| bootstrap / --no-build          | _Unimplemented_                    |
| bootstrap / --use-ssh           | _Unimplemented_                    |
| bootstrap / --use-submodules    | _Unimplemented_                    |
| bootstrap / --no-use-binaries   | Won't implement. Note 1            |
| bootstrap / --color             | Implemented                        |
| bootstrap / --project-directory | _Unimplemented_                    |
| bootstrap / [dependencies]      | Implemented                        |
| build                           | Implemented                        |
| build / --configuration         | Implemented                        |
| build / --platform              | Implemented                        |
| build / --derived-data          | _Unimplemented_                    |
| build / --no-skip-current       | _Unimplemented_                    |
| build / --color                 | Implemented                        |
| build / --project-directory     | _Unimplemented_                    |
| build / [dependencies]          | _Unimplemented_                    |
| checkout                        | Implemented                        |
| checkout / --use-ssh            | _Unimplemented_                    |
| checkout / --use-submodules     | _Unimplemented_                    |
| checkout / --no-use-binaries    | Won't implement. Note 1            |
| checkout / --color              | Implemented                        |
| checkout / --project-directory  | _Unimplemented_                    |
| checkout / [dependencies]       | Implemented                        |
| copy-frameworks                 | _Unimplemented_                    |
| fetch                           | _Unimplemented_                    |
| fetch / --color                 | _Unimplemented_                    |
| outdated                        | _Unimplemented_                    |
| outdated / --use-ssh            | _Unimplemented_                    |
| outdated / --verbose            | _Unimplemented_                    |
| outdated / --color              | _Unimplemented_                    |
| outdated / --project-directory  | _Unimplemented_                    |
| update                          | Implemented                        |
| update / --configuration        | Implemented                        |
| update / --platform             | Implemented                        |
| update / --derived-data         | _Unimplemented_                    |
| update / --verbose              | Implemented                        |
| update / --no-checkout          | _Unimplemented_                    |
| update / --no-build             | _Unimplemented_                    |
| update / --use-ssh              | _Unimplemented_                    |
| update / --use-submodules       | _Unimplemented_                    |
| update / --no-use-binaries      | Won't implement. Note 1            |
| update / --color                | Implemented                        |
| update / --project-directory    | _Unimplemented_                    |
| update / [dependencies]         | Implemented                        |

### Notes:

1. Binary archives will not be supported until Swift supports a non-fragile ABI.

## Roadmap

The current roadmap for Punic is as follows (in rough order of priority):

- [X] Support branch style Cartfile specifications.
- [ ] `copy-frameworks` subcommand.
- [ ] Run on travis
- [ ] Reliability. Punic needs to be tested against as many other Cartfiles as possible and needs to reliably produce the same build order
- [ ] Support `build` subcommand's `--no-skip-current` switch
- [ ] `fetch` subcommand
- [ ] Support specifying target dependencies at command line. (This is relatively low priority because incremental Punic builds are much much quicker than slow carthage clean builds.)
- [ ] Support `Cartfile.private` functionality
- [ ] Replace Cartfiles with a better, more expressive file format (yaml? toml?). Partially done.
- [ ] Add a `migrate` subcommand that can migrate Cartfiles to the new format.
- [X] Allow specification of default platforms and configurations in new style config file (`punic.yaml`)
- [ ] Cache xcodeproject and scheme info in new style build artifact files (replacing .resolved)

## New Features

TODO: Discuss differences between punic and carthage here.

## Configuration

TODO: Discuss `punic.yaml` here.

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
