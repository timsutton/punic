# Version History

## 0.2.0

* WIP

## 0.1.21

* Better filtering of semantic versions in a projects tags. Fixes #14
* Uploaded on https://pypi.python.org/pypi

## 0.1.20

* Fixes #13 - versions with semver identifiers (e.g. `v5.0.0-beta6`) now are parsed and compared correctly.
* Added some more unit tests for non-github project identifiers.

## 0.1.19


* Minor changes to README. Otherwise identical to 0.1.18 (made to combine two branches).

## 0.1.18

* Make sub-project Build symlinks relative (fixes #11)
* `punic init` is back and still as broken as ever.
* Large logging cleanup and bug fix - upshot is `--no-color` works again
* Adds a full `punic update` to test suite.
* Fixes punic on Python 3.5 which was a little bit broken.
* Fixes #8 - show a useful error if user doesn't have graphviz and/or pydotplus installed.

## 0.1.17

* Really fixes problems with ReactiveCocoa
* And in fact everything.
* Do not use 0.1.16 :-)

## 0.1.16

* Import bug fixes.
* Most importantly fixes problems with projects such as ReactiveCocoa. See https://github.com/schwa/punic/commit/75b7372c4926f1b6911a5e0e540d1311acda33e3 for more information.
* Fixes problem with `--platform` switch. 

## 0.1.15

* Fixes bug with platform being overiden if specified in punic.yaml and not command-line.

## 0.1.14

* Minor bug fixes. Thanks to @samsonjs and @Dschee for help.

## 0.1.13

* Removes broken `punic init`. Coming back later.
* Adds more control in `punic version`
* `punic copy_frameworks` strips out Headers, PrivateHeaders and Modules when copying frameworks

## 0.1.12

* Adds `--force` switch to `punic cache publish`.
* Fixes problem with configurations passed on command line
* General bug fixes, cleanup & refactoring.

## 0.1.11

* Adds `skips` section to `punic.yaml`. See README.
* Adds `punic list` command to list all schemes, projects, etc etc.
* Fixes bug with logs directory location.

## 0.1.10

* Fixes problem with --use-ssh

## 0.1.9

* Adds `--use-submodules`.
* Adds `--use-ssh`
* General bug fixes, cleanup & refactoring.

## 0.1.8

* Adds `--dry-run` flag to `build`
* "Library" directory is now `~/Library/Application Support/io.schwa.punic/`
* Fixes problem with "strange" Xcodeproj (e.g. https://github.com/NSProgrammer/ZipUtilities's Xcodeproj)
* General bug fixes, cleanup & refactoring.

## 0.1.7

* Supports `Cartfile.private` files.
* Adds support for `--toolchain` switch.
* General bug fixes, cleanup & refactoring.

## 0.1.6

* General bug fixes, cleanup & refactoring.

## 0.1.5 & Earlier

* Development
