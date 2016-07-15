
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
