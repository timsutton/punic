__author__ = 'schwa'
__all__ = ['Punic', 'Repository']

import re
import shlex
import subprocess
import logging
import os
import shutil

from pathlib2 import Path
import pygit2
from memoize import mproperty

from punic.utilities import *
from punic.xcode import *
from punic.types import *
from punic.runner import *
from punic.resolver import *
from punic.config import *

from copy import copy

########################################################################################################################


class Punic(object):
    def __init__(self, root_path = None):

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

        runner.cache_path = self.library_directory / "cache.shelf"

        root_project_identifier = ProjectIdentifier(project_name=self.root_path.name)

        self.all_repositories = {
            root_project_identifier: Repository(punic=self, identifier=root_project_identifier, repo_path=self.root_path),
        }

        self.root_project = self.repository_for_identifier(root_project_identifier)


    def resolve(self):
        logging.debug("#### Resolving")
        build_order = Resolver(self).resolve()

        for index, value in enumerate(build_order):
            dependency, version = value
            logging.debug('# {} {} {}'.format(index + 1, dependency, version.tag if version else ''))

        specifications = [Specification(identifier = dependency, predicate = VersionPredicate('"{}"'.format(version.tag))) for dependency, version in build_order[:-1]]
        logging.debug("# Saving Cartfile.resolved")

        cartfile = Cartfile(specifications = specifications)
        cartfile.write((self.root_path / 'Cartfile.resolved').open('w'))

    def fetch(self):
        logging.debug("#### Fetching")

        # TODO: FIXME
        for project in self.xcode_projects(fetch = True):
            pass

    @property
    def xcode_arguments(self):
        return {
                    'ONLY_ACTIVE_ARCH': 'NO',
                    'BITCODE_GENERATION_MODE': 'bitcode',
                    'CODE_SIGNING_REQUIRED': 'NO',
                    'CODE_SIGN_IDENTITY': '',
                    'CARTHAGE': 'YES',
                }

    def build(self, configuration, platforms):
        # TODO: This code needs a major refactoring and clean-up.

        if not self.build_path.exists():
            self.build_path.mkdir(parents = True)

        for platform, project, scheme in self.scheme_walker(configuration, platforms, fetch = False):
            with timeit(project.path.name):
                logging.debug('#' * 80)
                logging.debug('# Building {} {}'.format(project.path.name, scheme))

                ########################################################################################################

                products = dict()
                for sdk in platform.sdks:
                    logging.debug('# Building {} {} {} {}'.format(project.path.name, scheme, sdk, configuration))
                    product = project.build(scheme=scheme, configuration=configuration, sdk=sdk, arguments=self.xcode_arguments, temp_symroot = False)
                    products[sdk] = product

                ########################################################################################################

                device_sdk = platform.sdks[0] # By convention sdk[0] is always the device sdk (e.g. 'iphoneos' and not 'iphonesimulator')
                device_product = products[device_sdk]

                ########################################################################################################

                output_product = copy(device_product)
                output_product.target_build_dir = self.build_path / platform.output_directory_name

                ########################################################################################################

                logging.debug('# Copying binary')
                if output_product.product_path.exists():
                    shutil.rmtree(str(output_product.product_path))
                shutil.copytree(str(device_product.product_path), str(output_product.product_path))

                ########################################################################################################

                if len(products) > 1:
                    logging.debug('# Lipoing')
                    executable_paths = [product.executable_path for product in products.values()]
                    command = ['/usr/bin/xcrun', 'lipo', '-create'] + executable_paths + ['-output', output_product.executable_path]
                    runner.run(command)
                    mtime = executable_paths[0].stat().st_mtime
                    os.utime(str(output_product.executable_path), (mtime, mtime))

                ########################################################################################################

                logging.debug('# Copying swiftmodule files')
                for product in products.values():
                    for path in product.module_paths:
                        relative_path = path.relative_to(product.product_path)
                        shutil.copyfile(str(path), str(output_product.product_path / relative_path ))

                ########################################################################################################

                logging.debug('# Copying bcsymbolmap files')
                for product in products.values():
                    for path in product.bcsymbolmap_paths:
                        shutil.copy(str(path), str(output_product.target_build_dir))

                ########################################################################################################

                logging.debug('# Producing dSYM files')
                command = ['/usr/bin/xcrun', 'dsymutil', str(output_product.executable_path), '-o', str(output_product.target_build_dir / (output_product.executable_name + '.dSYM'))]
                runner.run(command)

                ########################################################################################################

#            exit(0)

    def clean(self, configuration, platforms):
        logging.debug("#### Cleaning")
        for platform, project, scheme in self.scheme_walker(configuration, platforms, fetch = False):
            for sdk in platform.sdks:
                command = xcodebuild(project = project.path, command = 'clean', scheme = scheme, sdk = sdk, configuration = configuration)
                runner.run(command)

    def xcode_projects(self, fetch = False):

        if not self.build_path.exists():
            self.build_path.mkdir(parents = True)

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

            if fetch:
                project.checkout(revision)
                logging.debug('# Copying project to Carthage/Checkouts')
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
            logging.debug('# Symlinking: {} {}'.format(self.build_path, carthage_symlink_path))
            assert self.build_path.exists()
            os.symlink(str(self.build_path), str(carthage_symlink_path))

            def make_identifier(project_path):
                rev = project.repo.revparse_single(revision).id
                identifier = '{},{}'.format(str(rev), project_path.relative_to(self.checkouts_path))
                return identifier

            project_paths = checkout_path.glob("*.xcodeproj")
            projects = [XcodeProject(self, project_path, make_identifier(project_path)) for project_path in project_paths]
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
        logging.debug('# Checking out {} @ revision {}'.format(self, revision))
        rev = self.repo.revparse_single(revision)
        self.repo.checkout_tree(rev, strategy=pygit2.GIT_CHECKOUT_FORCE)

    def fetch(self):
        if not self.path.exists():
            with work_directory(str(self.path.parent)):
                logging.debug('# Cloning: {}'.format(self))
                runner.run('git clone --recursive "{}"'.format(self.identifier.remote_url))
                logging.debug('# Cloned: {}'.format(self))
        else:
            with work_directory(str(self.path)):
                logging.debug('# Fetching: {}'.format(self))
                command = 'git fetch'
                command = shlex.split(command)
                subprocess.check_output(command)

    def specifications_for_tag(self, tag):
        # type: (Tag) -> [Specification]

        #logging.debug('Getting cartfile from tag {} of {}'.format(tag, self))

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
