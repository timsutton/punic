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

## New Features

### `punic.yaml` files.

As well as configuring your build dependencies with `Cartfile` you can also use a `punic.yaml` file to specify other options.

#### `punic.yaml` defaults

An example `punic.yaml` file follows:

```yaml
defaults:
  configuration: Debug
  platform: iOS
```

This example specifies both a default configuration and a default platform. This allows you to skip providing `--configuration` and `--platform` switches on the command-line.

Switches provided on the command line will override defaults in your `punic.yaml` file.

#### `punic.yaml` repo-overrides

Assume you have a project that depends on an external repository "ExampleOrg/Project-A" which in turns depends on another external repository "ExampleOrg/Project-B". If you wanted to fork and make changes to "Project-B" you would also have to fork and change the Cartfile within "Project-A" so that it refers to the forked URL of "Project-B".

With the `repo-overrides` section of `punic.yaml` you can globally replace the URL of any dependency without having to edit Cartfiles deep within your dependency hierarchy.

```yaml
repo-overrides:
  Project-B: git@github.com:MyOrg/Project-B.git
```

You can also use this feature to redirect a dependency to a local, on disk url. This is useful if you need to test changes inside a dependency.

```yaml
repo-overrides:
  Project-B: file:///Users/example/Projects/Project-B
```

Note that repositories pointed to by file URL are still cloned and fetched just like any other repository and your changes _must_ be committed for them to be picked up by Punic.

## Roadmap

The current roadmap for Punic is as follows (in rough order of priority):

- [X] `copy-frameworks` subcommand.
- [ ] `fetch` subcommand
- [ ] Add a `migrate` subcommand that can migrate Cartfiles to the punic.yaml.
- [ ] Add a `table-of-contents` subcommand that will produce a filtered list of all projects, schemes etc of all dependencies. This TOC could then be used inside punic.yaml as a whitelist or blacklist. This will allow us to do things like skip frameworks that should not be built.
- [ ] Include full Cartfile (.private) functional in punic.yaml
- [ ] Provide carthage compatibility mode and break punic command line compatibility. For example 'bootstrap' should be renamed 'update' (and update becomes something else).
- [ ] Reliability. Punic needs to be tested against as many other Cartfiles as possible and needs to reliably produce the same build order
- [ ] Run on travis
- [ ] Support `build` subcommand's `--no-skip-current` switch
- [ ] Support `Cartfile.private` functionality
- [ ] Support specifying target dependencies at command line. Full resolve/fetch
- [ ] Unit test Resolver
- [X] Allow specification of default platforms and configurations in new style config file (`punic.yaml`)
- [X] Support branch style Cartfile specifications.
- [X] Support specifying target dependencies at command line. Building only.

## Differences between Punic & Carthage

Aside from differences of implementation one of the fundamental differences is that Carthage always runs `xcodebuild clean` before building dependencies. Punic deliberately does not perform this clean step and provides an explicit `punic clean` command. The goal of this is to not force collaborators to sit through long clean builds when very little has changed. This can provide dramatic speed ups to a users workflow (during testing builds that can take Carthage 20-25 minutes to build on top-end hardware take less than a minute to do a 'dirty' build.)

Punic only supports "github" style dependency specifications and does not support the use of branch names in version specifications.

A complete list of Carthage compatibility as of version 0.16.2 of Carthage follows:

| Command/Switch                  | Status                             |
| ---------------                 | ---------------------------------- |
| archive                         | _Won't_ implement. Note 1          |
| bootstrap                       | Implemented                        |
| bootstrap / --configuration     | Implemented                        |
| bootstrap / --platform          | Implemented                        |
| bootstrap / --toolchain         | _Unimplemented_                    |
| bootstrap / --derived-data      | _Unimplemented_                    |
| bootstrap / --verbose           | Implemented. Note 4                |
| bootstrap / --no-checkout       | _Unimplemented_                    |
| bootstrap / --no-build          | _Unimplemented_                    |
| bootstrap / --use-ssh           | _Unimplemented_                    |
| bootstrap / --use-submodules    | _Unimplemented_                    |
| bootstrap / --no-use-binaries   | _Won't_ implement. Note 1          |
| bootstrap / --color             | Implemented. Note 4                |
| bootstrap / --project-directory | _Unimplemented_                    |
| bootstrap / [dependencies]      | Partially implemented. Note 3      |
| build                           | Implemented                        |
| build / --configuration         | Implemented                        |
| build / --platform              | Implemented                        |
| build / --toolchain             | _Unimplemented_                    |
| build / --derived-data          | _Unimplemented_                    |
| build / --no-skip-current       | _Unimplemented_                    |
| build / --color                 | Implemented. Note 4                |
| build / --verbose               | Implemented. Note 4                |
| build / --project-directory     | _Unimplemented_                    |
| build / [dependencies]          | Partially implemented. Note 3      |
| checkout                        | Implemented                        |
| checkout / --use-ssh            | _Unimplemented_                    |
| checkout / --use-submodules     | _Unimplemented_                    |
| checkout / --no-use-binaries    | _Won't_ implement. Note 1          |
| checkout / --color              | Implemented. Note 4                |
| checkout / --verbose            | Implemented. Note 4                |
| checkout / --project-directory  | _Unimplemented_                    |
| checkout / [dependencies]       | _Unimplemented_                    |
| copy-frameworks                 | Implemented                        |
| fetch                           | _Won't_ implement. Note 1          |
| help                            | Implemented. Note 5                |
| outdated                        | _Unimplemented_                    |
| outdated / --use-ssh            | _Unimplemented_                    |
| outdated / --verbose            | _Unimplemented_                    |
| outdated / --color              | _Unimplemented_                    |
| outdated / --project-directory  | _Unimplemented_                    |
| update                          | Implemented                        |
| update / --configuration        | Implemented                        |
| update / --platform             | Implemented                        |
| update / --toolchain            | _Unimplemented_                    |
| update / --derived-data         | _Unimplemented_                    |
| update / --verbose              | Implemented. Note 4                |
| update / --no-checkout          | _Unimplemented_                    |
| update / --no-build             | _Unimplemented_                    |
| update / --use-ssh              | _Unimplemented_                    |
| update / --use-submodules       | _Unimplemented_                    |
| update / --no-use-binaries      | _Won't_ implement. Note 1          |
| update / --color                | Implemented. Note 4                |
| update / --project-directory    | _Unimplemented_                    |
| update / [dependencies]         | Partially implemented. Note 3      |


### Notes:

1. Binary archives will not be supported until Swift supports a non-fragile ABI.
2. `carthage fetch` doesn't seem very useful.
3. Specifying dependencies only works to limit what is built. It does not prevent unspecified dependencies from being fetched.
4. Unlike carthage both the `--verbose` and `--color` are both passed to punic _before_ the subcommand name. e.g. `punic --color --verbose update`. Carthage expects these switches after the subcommand name.
5. Help is implemented as `punic --help` and not as its own subcommand.

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
