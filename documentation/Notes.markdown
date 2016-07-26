
A complete list of Carthage compatibility as of version 0.16.2 of Carthage follows:

| Command/Switch                  | Status                             |
| ------------------------------- | ---------------------------------- |
| archive                         | _Won't_ implement. Note 1          |
| bootstrap                       | ✅ Implemented. Note 10            |
| build                           | ✅ Implemented                     |
| build / --configuration         | ✅ Implemented                     |
| build / --platform              | ✅ Implemented                     |
| build / --toolchain             | ❗️ _Unimplemented_                  |
| build / --derived-data          | ✅ Implemented. Note 6             |
| build / --no-skip-current       | ❗️ _Unimplemented_                 |
| build / --color                 | ✅ Implemented. Note 4             |
| build / --verbose               | ✅ Implemented. Note 4             |
| build / --project-directory     | ❗️ _Unimplemented_                 |
| build / [dependencies]          | Partially implemented. Note 3      |
| checkout                        | ✅ Implemented                     |
| checkout / --use-ssh            | ✅ Implemented. Note 8             |
| checkout / --use-submodules     | ❗️ _Unimplemented_                 |
| checkout / --no-use-binaries    | ❗️ _Won't_ implement. Note 1       |
| checkout / --color              | ✅ Implemented. Note 4             |
| checkout / --verbose            | ✅ Implemented. Note 4             |
| checkout / --project-directory  | ❗️ _Unimplemented_                 |
| checkout / [dependencies]       | ❗️ _Unimplemented_                 |
| copy-frameworks                 | ✅ Implemented                     |
| fetch                           | _Won't_ implement. Note 1          |
| help                            | ✅ Implemented. Note 5             |
| outdated                        | _Won't_ implement. Note 9          |
| update                          | ✅ Implemented                     |
| update / --configuration        | ✅ Implemented                     |
| update / --platform             | ✅ Implemented                     |
| update / --toolchain            | ❗️ _Unimplemented_                 |
| update / --derived-data         | ✅ Implemented. Note 6             |
| update / --verbose              | ✅ Implemented. Note 4             |
| update / --no-checkout          | ✅ Implemented. Note 7             |
| update / --no-build             | ✅ Implemented. Note 7             |
| update / --use-ssh              | ✅ Implemented. Note 8             |
| update / --use-submodules       | ❗️ _Unimplemented_                 |
| update / --no-use-binaries      | _Won't_ implement. Note 1          |
| update / --color                | ✅ Implemented. Note 4             |
| update / --project-directory    | _Unimplemented_                    |
| update / [dependencies]         | Partially implemented. Note 3      |


### Notes:

1. Binary archives will not be supported until Swift supports a non-fragile ABI.
2. `carthage fetch` doesn't seem very useful.
3. Specifying dependencies only works to limit what is built. It does not prevent unspecified dependencies from being fetched.
4. Unlike carthage both the `--verbose` and `--color` are passed to punic _before_ the subcommand name. e.g. `punic --color --verbose update`. Carthage expects these switches after the subcommand name.
5. Help is implemented as `punic --help` and not as its own subcommand.
6. All punic builds use a unique derived-data directory. There is no need to specify this manually. It is not currently possible to override this.
7. `carthage update`'s `--no-build` and `--no-checkout` can all be simulated by various calls to `punic resolve`, `punic build`. We've decided that Carthage's default set of sub-commands was confusing and unwieldy so have supplied our what we believe to be a more streamlined set of subcommands.
8. ssh is the default mode for punic repos. Currently it is not possible to not use ssh
9. We have no plans to implement an `outdated` subcommand
10. We have replaced the `bootstrap` command with the punic's extended `build` command. See the FAQ section of the README.
