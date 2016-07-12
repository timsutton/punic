__author__ = 'Jonathan Wight <jwight@mac.com>'
__all__ = ['Punic']

import logging
import os
import shutil
from copy import copy

from pathlib2 import Path
import requests

import punic
from punic.utilities import *
from punic.xcode import *
from punic.basic_types import *
from punic.runner import *
from punic.resolver import *
from punic.config import *
from punic.repository import *

########################################################################################################################


class Punic(object):
    def __init__(self, root_path = None):

        if not root_path:
            root_path = Path.cwd()

        self.config = Config()

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

        try:
            logging.debug('# Checking punic version')
            current_version, latest_version = self.versions()
            logging.debug('# Current version: {}, latest version: {}'.format(current_version, latest_version))
            if current_version < latest_version:
                logging.warn('# You are using version {}, version {} is available. Use `pip install -U http://github.com/schwa/punic` to update to latest version.'.format(current_version, latest_version))
        except Exception, e:
            logging.debug('# Failed to check versions: {}'.format(e))

    def versions(self):
        # type: () -> (SemanticVersion, SemanticVersion)

        current_version = SemanticVersion.string(punic.__version__)
        # TODO: Is this the best URL?
        result = requests.get('https://raw.githubusercontent.com/schwa/punic/develop/VERSION', timeout=0.3)
        latest_version = SemanticVersion.string(result.text.strip())

        return current_version, latest_version


    def resolve(self, fetch):
        # type: (bool)
        resolver = Resolver(punic = self, fetch = fetch)
        build_order = resolver.resolve_build_order()

        for index, value in enumerate(build_order):
            dependency, version = value
            logging.debug('# {} {} {}'.format(index + 1, dependency, version.revision if version else ''))

        specifications = [Specification(identifier = dependency, predicate = VersionPredicate('"{}"'.format(version.revision))) for dependency, version in build_order[:-1]]
        logging.debug("# Saving Cartfile.resolved")

        cartfile = Cartfile(specifications = specifications)
        cartfile.write((self.root_path / 'Cartfile.resolved').open('w'))

    def graph(self, fetch = True):
        # type: (bool) -> DiGraph
        resolver = Resolver(punic = self, fetch = fetch)
        return resolver.resolve()

    def fetch(self):
        # type: ()
        # TODO: FIXME
        for project in self.xcode_projects(fetch = True):
            pass

    @property
    def xcode_arguments(self):
        # type: () -> dict
        return {
                    'ONLY_ACTIVE_ARCH': 'NO',
                    'BITCODE_GENERATION_MODE': 'bitcode',
                    'CODE_SIGNING_REQUIRED': 'NO',
                    'CODE_SIGN_IDENTITY': '',
                    'CARTHAGE': 'YES',
                }

    def build(self, dependencies, fetch):
        # type: ([str], bool)
        # TODO: This code needs a major refactoring and clean-up.

        configuration, platforms = self.config.configuration, self.config.platforms

        if not self.build_path.exists():
            self.build_path.mkdir(parents = True)

        filtered_dependencies = self.ordered_dependencies(fetch = False, name_filter= dependencies)

        projects = self.xcode_projects(dependencies = filtered_dependencies, fetch = fetch)

        for platform, project, scheme in self.scheme_walker(projects = projects, configuration = configuration, platforms = platforms):

            with timeit(project.path.name):

                products = dict()
                for sdk in platform.sdks:
                    logging.info('# Building {} {} {} {}'.format(project.path.name, scheme, sdk, configuration))
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
                    logging.debug('# Lipo-ing')
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
        # type: (str, str) -> DiGraph
        logging.debug("#### Cleaning")

        for platform, project, scheme in self.scheme_walker(configuration = configuration, platforms = platforms):
            for sdk in platform.sdks:
                command = xcodebuild(project = project.path, command = 'clean', scheme = scheme, sdk = sdk, configuration = configuration)
                runner.run(command)

    def ordered_dependencies(self, fetch = False, name_filter = None):
        # type: (bool, [str]) -> [(ProjectIdentifier, Revision)]

        cartfile = Cartfile()
        cartfile.read(self.root_path / 'Cartfile.resolved')

        def predicate_to_revision(predicate):
            # type: (VersionPredicate) -> Revision

            if predicate.operator == VersionOperator.commitish:
                return Revision(repository=None, revision=predicate.value, revision_type=Revision.Type.other)
            else:
                raise Exception("Cannot convert predicate to revision: {}".format(predicate))

        dependencies = [(spec.identifier, predicate_to_revision(spec.predicate)) for spec in cartfile.specifications]
        resolver = Resolver(self)
        resolved_dependencies = resolver.resolve_versions(dependencies, fetch = fetch)
        resolved_dependencies = [dependency for dependency in resolved_dependencies if dependency[0].matches(name_filter)]
        return resolved_dependencies

    def xcode_projects(self, dependencies = None, fetch = False):
        # type: ([(ProjectIdentifier, Revision)]) -> [XcodeProject]

        if not self.build_path.exists():
            self.build_path.mkdir(parents = True)
        all_projects = []

        if not dependencies:
            dependencies = self.ordered_dependencies(fetch = fetch)

        for (identifier, revision) in dependencies:
            project = self.repository_for_identifier(identifier)
            revision = revision.revision
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
            logging.debug('# Creating symlink: {} {}'.format(self.build_path, carthage_symlink_path))
            assert self.build_path.exists()
            os.symlink(str(self.build_path), str(carthage_symlink_path))

            def make_identifier(project_path):
                rev = project.rev_parse(revision)
                identifier = '{},{}'.format(str(rev), project_path.relative_to(self.checkouts_path))
                return identifier

            project_paths = checkout_path.glob("*.xcodeproj")
            projects = [XcodeProject(self, project_path, make_identifier(project_path)) for project_path in project_paths]
            all_projects += projects
        return all_projects

    def scheme_walker(self, projects = None, configuration = None, platforms = None):
        # type: ([XcodeProject], str, [Platform]) -> (str, XcodeProject, str)

        if not projects:
            projects = self.xcode_projects(fetch=False)

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
        # type: (ProjectIdentifier, Revision, bool) -> [ProjectIdentifier, [Revision]]

        repository = self.repository_for_identifier(identifier, fetch = fetch)
        specifications = repository.specifications_for_revision(tag)

        def make(specification):
            repository = self.repository_for_identifier(specification.identifier, fetch = fetch)
            tags = repository.revisions_for_predicate(specification.predicate)

            if specification.predicate.operator == VersionOperator.commitish:
                tags.append(Revision(repository=repository, revision=specification.predicate.value, revision_type=Revision.Type.other))
                tags.sort()

            assert len(tags)
            return repository.identifier, tags

        return [make(specification) for specification in specifications]
