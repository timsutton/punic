# Version History

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
