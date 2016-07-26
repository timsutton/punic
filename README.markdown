# punic [![Travis][image_1]][link_1] [![license][image_2]][link_2] [![tag][image_3]][link_3]

[image_1]: https://img.shields.io/travis/schwa/punic.svg
[link_1]: https://travis-ci.org/schwa/punic/branches
[image_2]: https://img.shields.io/github/license/schwa/punic.svg
[link_2]: https://github.com/schwa/punic/blob/master/LICENSE
[image_3]: https://img.shields.io/github/tag/schwa/punic.svg
[link_3]: https://github.com/schwa/punic/releases

## Description

Punic is intended to be an easier to use, faster and more reliable implementation of the [Carthage](http://github.com/carthage/carthage) dependency management system.

## Caveat!!!

Punic can be considered an early preview release and probably is not ready for production use. Use at your own peril.

## Installation

Quick install (for [homebrew](http://brew.sh) users):

```shell
$ brew update
$ brew install python
$ brew install libyaml
$ pip install --upgrade git+https://github.com/schwa/punic.git
```

Punic is python 3(.5) compatible too.

```shell
$ brew update
$ brew install python3
$ brew install libyaml
$ pip3 install --upgrade git+https://github.com/schwa/punic.git
```

If you have an error installing punic run pip again with the verbose flag (`pip install --upgrade git+https://github.com/schwa/punic.git`) and create an [issue](https://github.com/schwa/punic/issues).

Note be careful installing punic (and in face _all_ python software) with `sudo`. In fact installing with `sudo` is not explicitly supported.

Installing punic inside a python virtualenv is supported but you might have difficulty if you try to execute a virtualenv-ed punic from Xcode (e.g. `punic copy-frameworks`).

## Usage

Punic has built-in help:

```shell
$ punic --help
Usage: punic [OPTIONS] COMMAND [ARGS]...

Options:
  --echo                Echo all commands to terminal.
  --verbose             Verbose logging.
  --color / --no-color  TECHNICOLOR.
  --help                Show this message and exit.

Commands:
  build            Fetch and build the project's dependencies.
  clean            Clean project & punic environment.
  copy-frameworks  In a Run Script build phase, copies each...
  fetch            Fetch the project's dependencies..
  graph            Output resolved dependency graph.
  init             Generate punic configuration file.
  resolve          Resolve dependencies and output...
  update           Update and rebuild the project's...
  version          Display the current version of Carthage.
```

Each sub-command also has built in help:

```shell
$ punic build --help
schwa@orthanc ~/D/TEst> punic build --help
Usage: punic build [OPTIONS] [DEPS]...

  Fetch and build the project's dependencies.

Options:
  --configuration TEXT  Dependency configurations to build. Usually 'Release'
                        or 'Debug'.
  --platform TEXT       Platform to build. Comma separated list.
  --fetch / --no-fetch  Controls whether to fetch dependencies.
  --help                Show this message and exit.
```

To make your Xcode project consume other Carthage compatible dependencies add a file called `Cartfile` at the root level of your project. For example:

```
github "AlamoFire/AlamoFire"
github "realm/realm-cocoa"
```

TODO: See carthage documentation for exact syntax.

A `Cartfile` isn't required to exactly specify what version of which dependency it requires, To do that you can manually resolve your dependencies:

```shell
punic resolve
```

This resolve step creates a new file called `Carthage.resolved`. Using the above file as input the `Cartfile.resolved` contains the following:

```
github "AlamoFire/AlamoFire" "3.4.1"
github "realm/realm-cocoa" "v1.0.2"
```

Note that the resolve sub-command has to fetch all dependencies. This can take a while the first time you run it.

You generally do not need to manually invoke `punic resolve` - it is usually automatically performed for you as part of an update. See later.

To checkout and build your dependencies run `punic build`. For example

```shell
punic build --platform iOS --configuration Debug
```

This fetches the latest versions of all dependencies and then builds them.

You can only build your dependencies if your dependencies have been resolved (i.e. there's a `Cartfile.resolved` file in your project's directory).

You should run `punic build` when:

* You first clone a punic enabled project
* Your `Carthage.resolved` file has changed (perhaps you fetched some changes from another developer)

If you know punic already has the correct dependencies checked out you can run build with the `--no-fetch` switch:

```shell
punic build --platform iOS --configuration Debug --no-fetch
```

Note that you can specify a platform and a configuration for `punic build`. If you fail to specify a platform then all platforms will be compiled. If you fail to specify a configuration then the dependency's default will be used (this is usually "Release").

If you always specify the same platform and configuration for builds you can create a `punic.yaml` file in the same directory as your `Cartfile`:

```yaml
defaults:
  configuration: Debug
  platform: iOS
```

You can use `punic init` to help you generate a `punic.yaml` (TODO: We intend `punic.yaml` will increase in expressiveness over time)

If you want to perform a quick clean of a project (deleting the project's "Derived Data" directory) you can use the following:

```shell
punic clean
```

Running `punic resolve` then `punic build` together is a common operation and have been combined into the `punic update` sub-command:

```shell
punic update
```

See https://github.com/Carthage/Carthage for usage information


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
- [X] `fetch` subcommand
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


## Frequently Answer Questions

### Where did the `bootstrap` command go?

Bootstrap proved to be confusing with users believing they should only run it once per project and not whenever the `Cartfile.resolved` has changed. It has been replaced by the `build` subcommand. The previous behavior of the build subcommand can be reproduced with: `punic build --no-fetch`.

### Why can't I specify use the `--derived-data` switch?

It seems best to always use a custom derived data directory for punic builds. This keeps punic builds of dependencies separated from your own builds. It also allows punic to very quickly clean the derived-data directory.

### Where does punic store keep everything?

```
<project-dir>/
    Cartfile
    Cartfile.resolved
    Carthage/
        Build/
        Checkouts/
    punic.yaml
~/Library/io.schwa.punic/
    DerivedData/
    cache.shelf
    repo_cache/
```

### Why rewrite Carthage?

Carthage has had some rather severe performance and stability issues that have made it very hard to reliably use in production. These issues have historically proven very hard for the maintainers of Carthage to address. Instead of contributing fixes to Carthage it was deemed quicker and easier to produce a new clean room implementation of the concepts pioneered by the Carthage developers

(TODO: Link to Carthage issues.)

### What about Swift Package Manager?

Swift Package Manager is currently in its very early days and it will be a while before SPM is ready to be used to ship software. Until then Carthage and Punic still serve an important role.

### Why not use Cocoapods?

No thank you.

### Why Python and not Swift?

TODO: ~7000 lines of swift in Carthage (excluding dependencies) vs ~1000 lines of Python in Punic.
TODO: Batteries included
TODO: bootstrap problems

## License

MIT
