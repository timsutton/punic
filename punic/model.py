__author__ = 'schwa'
__all__ = ['Punic', 'Specification', 'Repository']

import re
import shlex
import subprocess
import logging
from pathlib2 import Path
import pygit2
import os
import shutil
from memoize import mproperty

from punic.utilities import *
from punic import xcode

from resolver import *

from config import *

# TODO: Really simple logging config for now.
logging.basicConfig(format='%(message)s', level=logging.DEBUG)


########################################################################################################################


class Punic(object):
    def __init__(self, root_path = None):
        # root_path: (Path)

        if not root_path:
            root_path = Path.cwd()

        self.root_path = root_path  # type: Path
        self.library_directory = Path(os.path.expanduser('~/Library/io.schwa.Punic'))
        if not self.library_directory.exists():
            self.library_directory.mkdir(parents=True)
        self.repo_cache_directory = self.library_directory / 'repo_cache'
        if not self.repo_cache_directory.exists():
            self.repo_cache_directory.mkdir(parents=True)
        self.punic_path = self.root_path / 'Carthage'
        self.build_path = self.punic_path / 'Build'
        self.checkouts_path = self.punic_path / 'Checkouts'
        self.cacheable_runner = CacheableRunner(path = self.library_directory / "cache.shelf")

        root_project_identifier = ProjectIdentifier(project_name=self.root_path.name)

        self.all_repositories = {
            root_project_identifier: Repository(punic=self, identifier=root_project_identifier, repo_path=self.root_path),
        }

        self.root_project = self.repository_for_identifier(root_project_identifier)

    def resolve(self):
        logging.info("#### Resolving")
        build_order = Resolver(self).resolve()

        for index, value in enumerate(build_order):
            dependency, version = value
            logging.info('# {} {} {}'.format(index + 1, dependency, version.tag if version else ''))

        specifications = [Specification(identifier = dependency, predicate = VersionPredicate('"{}"'.format(version.tag))) for dependency, version in build_order[:-1]]
        logging.info("# Saving Cartfile.resolved")

        cartfile = Cartfile(specifications = specifications)
        cartfile.write((self.root_path / 'Cartfile.resolved').open('w'))

    def fetch(self):
        logging.info("#### Fetching")

        for project in self.xcode_projects(fetch = True):
            pass

    def build(self, configuration, platforms):
        logging.info("#### Building")

        # cartfile = Cartfile()
        # cartfile.read((self.root_path / 'Cartfile'))

        for platform, project, scheme in self.scheme_walker(configuration, platforms, fetch = False):
            with timeit(project.path.name):
                platform_build_path = self.build_path / platform.output_directory_name
                logging.info('#' * 80)
                logging.info('# Building {} {}'.format(project.path.name, scheme))

                arguments = {
                    'ONLY_ACTIVE_ARCH': 'NO',
                    'BITCODE_GENERATION_MODE': 'bitcode',
                    'CODE_SIGNING_REQUIRED': 'NO',
                    'CODE_SIGN_IDENTITY': '',
                    'CARTHAGE': 'YES',
                }

                sdks = platform.sdks

                paths_for_sdk_build = dict()

                for sdk in sdks:
                    logging.info('# Building {}{} {} {}'.format(project.path.name, scheme, sdk, configuration))
                    executable_path = project.build(scheme=scheme, configuration=configuration, sdk=sdk, arguments=arguments, echo = False, temp_symroot = False)
                    paths_for_sdk_build[sdk] = executable_path

                logging.info('# Copying binary')
                final_path = platform_build_path / paths_for_sdk_build[sdks[0]].parent.name
                if final_path.exists():
                    shutil.rmtree(str(final_path))
                shutil.copytree(str(paths_for_sdk_build[sdks[0]].parent), str(final_path))

                if len(sdks) > 1:
                    logging.info('# Lipoing')

                    executable_paths = [path for path in paths_for_sdk_build.values()]

                    output_path = final_path / paths_for_sdk_build[sdks[0]].name
                    command = ['/usr/bin/xcrun', 'lipo', '-create'] + [str(path) for path in executable_paths ] + ['-output', str(output_path)]
                    run(command, echo = False)

                    mtime = executable_paths[0].stat().st_mtime
                    os.utime(str(output_path), (mtime, mtime))

                    logging.info('# Copying modules')
                    for sdk in sdks:
                        modules_source_path = paths_for_sdk_build[sdk].parent / "Modules/{}.swiftmodule".format(paths_for_sdk_build[sdk].name)
                        if modules_source_path.exists():
                            modules_destination_path = final_path / "Modules/{}.swiftmodule".format(paths_for_sdk_build[sdk].name)
                            for f in modules_source_path.glob("*"):
                                shutil.copyfile(str(f), str(modules_destination_path / f.name))

    def clean(self, configuration, platforms):
        logging.info("#### Cleaning")
        for platform, project, scheme in self.scheme_walker(configuration, platforms, fetch = False):
            for sdk in platform.sdks:
                command = xcode.xcodebuild(project = project.path, command = 'clean', scheme = scheme, sdk = sdk, configuration = configuration)
                run(command, echo = True)

    def xcode_projects(self, fetch = False):
        all_projects = []

        cartfile = Cartfile()
        cartfile.read(self.root_path / 'Cartfile.resolved')

        dependencies = [(spec.identifier, Tag(spec.predicate.value)) for spec in cartfile.specifications]

        resolver = Resolver(self)
        build_order = resolver.resolve_versions(dependencies, fetch = fetch)

        for (identifier, tag) in build_order:
            project = self.repository_for_identifier(identifier)

            revision = tag.tag

            checkout_path = self.checkouts_path / project.path.name

            if fetch == True:
                project.checkout(revision)
                logging.info('# Copying project to Carthage/Checkouts')
                if checkout_path.exists():
                    shutil.rmtree(str(checkout_path))
                shutil.copytree(str(project.path), str(checkout_path), ignore=shutil.ignore_patterns('.git'))

            if not checkout_path.exists():
                raise Exception('No checkout at path: {}'.format(checkout_path))

            # Make a Carthage/Build symlink inside checked out project.
            carthage_path = checkout_path / 'Carthage'
            if not carthage_path.exists():
                carthage_path.mkdir()

            carthage_symlink_path = carthage_path / 'Build'
            if carthage_symlink_path.exists():
                carthage_symlink_path.unlink()
            os.symlink(str(self.build_path), str(carthage_symlink_path ))


            def make_identifier(project_path):
                rev = project.repo.revparse_single(revision).id
                identifier = '{},{}'.format(str(rev), project_path.relative_to(self.checkouts_path))
                return identifier

            project_paths = checkout_path.glob("*.xcodeproj")
            projects = [xcode.Project(self, project_path, make_identifier(project_path)) for project_path in project_paths]
            all_projects += projects
        return all_projects

    def scheme_walker(self, configuration, platforms, fetch):
        projects = self.xcode_projects(fetch = fetch)
        for platform in platforms:
            platform_build_path = self.build_path / platform.output_directory_name
            if not platform_build_path.exists():
                platform_build_path.mkdir(parents=True)
            for project in projects:
                schemes = [scheme for scheme in project.schemes if
                           platform.sdks[0] in project.build_settings(scheme).get('SUPPORTED_PLATFORMS', '').split(' ')]
                schemes = [scheme for scheme in schemes if
                           project.build_settings(scheme).get('PACKAGE_TYPE') == 'com.apple.package-type.wrapper.framework']
                for scheme in schemes:
                    yield platform, project, scheme

    def repository_for_identifier(self, identifier, fetch = True):
        # type: (ProjectIdentifier) -> Repository
        if identifier in self.all_repositories:
            return self.all_repositories[identifier]
        else:
            path = self.repo_cache_directory / identifier.project_name
            repository = Repository(self, identifier=identifier, repo_path=path)
            if fetch:
                repository.fetch()
            self.all_repositories[identifier] = repository
            return repository

    def dependencies_for_project_and_tag(self, identifier, tag, fetch = True):
        repository = self.repository_for_identifier(identifier, fetch = fetch)
        specifications = repository.specifications_for_tag(tag)

        def make(specification):
            repository = self.repository_for_identifier(specification.identifier, fetch = fetch)
            tags = repository.tags_for_predicate(specification.predicate)
            return repository.identifier, tags

        return [make(specification) for specification in specifications]


########################################################################################################################

class Repository(object):
    def __init__(self, punic, identifier, repo_path):
        self.punic = punic
        self.identifier = identifier
        self.path = repo_path

    def __repr__(self):
        return str(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __lt__(self, other):
        return self.identifier < other.identifier

    def __hash__(self):
        return hash(self.identifier)

    @mproperty
    def repo(self):
        assert self.path.exists()
        return pygit2.Repository(str(self.path))

    @mproperty
    def tags(self):
        """Return a list of Tag objects representing git tags. Only tags that are valid semantic versions are returned"""
        # type: () -> [Tag]
        refs = self.repo.listall_references()
        regex = re.compile(r'^refs/tags/(.+)')
        refs = [ref for ref in refs if regex.match(ref)]
        refs = [regex.match(ref).group(1) for ref in refs]
        tags = [Tag(ref) for ref in refs if SemanticVersion.is_semantic(ref)]
        return sorted(tags)

    def checkout(self, revision):
        # type: (String)
        logging.info('# Checking out {} @ revision {}'.format(self, revision))
        rev = self.repo.revparse_single(revision)
        self.repo.checkout_tree(rev, strategy=pygit2.GIT_CHECKOUT_FORCE)

    def fetch(self):
        if not self.path.exists():
            with work_directory(str(self.path.parent)):
                logging.info('# Cloning: {}'.format(self))
                run('git clone --recursive "{}"'.format(self.identifier.remote_url))
                logging.info('# Cloned: {}'.format(self))
        else:
            with work_directory(str(self.path)):
                logging.info('# Fetching: {}'.format(self))
                command = 'git fetch'
                command = shlex.split(command)
                subprocess.check_output(command)

    def specifications_for_tag(self, tag):
        # type: (Tag) -> [Specification]

        #logging.info('Getting cartfile from tag {} of {}'.format(tag, self))

        if tag == None and self == self.punic.root_project:
            cartfile = Cartfile()
            cartfile.read(self.path / "Cartfile")
            return cartfile.specifications

        rev = self.repo.revparse_single(tag)
        if not hasattr(rev, 'tree'):
            rev = rev.get_object()
        if 'Cartfile' not in rev.tree:
            return []
        else:
            cartfile = rev.tree['Cartfile']
            blob = self.repo[cartfile.id]
            cartfile = Cartfile()
            cartfile.read(blob.data)
            return cartfile.specifications

    def tags_for_predicate(self, predicate):
        # type: (VersionPredicate) -> [Tag]
        return [tag for tag in self.tags if predicate.test(tag.semantic_version)]

########################################################################################################################
