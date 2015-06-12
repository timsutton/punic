__author__ = 'schwa'
__all__ = ["Punic", "Specification", "Dependency"]

import shutil
import os
import re
import shlex
import subprocess
import logging

from pathlib import Path
import pygit2

from utilities import *
from xcode import *

# TODO: Really simple logging config for now.
logging.basicConfig(format='%(message)s', level=logging.DEBUG)

class Punic(object):
    def __init__(self, root_path):
        self.root_path = root_path
        self.scratch_directory = Path(os.path.expanduser("~/Library/io.schwa.Punic/Scratch"))
        if not self.scratch_directory.exists():
            self.scratch_directory.mkdir(parents = True)
        self.build_path = self.root_path / "Carthage/Build"
        self.checkouts_path = self.root_path / "Carthage/Checkouts"

        self.spec_file_path = self.root_path / "Cartfile"
        self.resolved_spec_file_path = self.spec_file_path.with_suffix(".resolved")

    def read_spec_file(self, path):
        specifications = []
        for line in path.open().readlines():
            line = line.strip()
            match = re.match(r"^github .+", line)
            if match:
                specification = Specification(line)
                specifications.append(specification)
        return specifications

    @property
    def dependencies(self):
        if not hasattr(self, "_dependencies"):
            self._dependencies = []

            cartfile = self.root_path / "Cartfile"
            for line in cartfile.open().readlines():
                line = line[:-1]
                match = re.match(r"^github .+", line)
                if match:
                    dependency = Dependency(self, line)
                    self._dependencies.append(dependency)

        return self._dependencies

    def update(self):
        logging.info("# Updating dependencies")
        for dependency in self.dependencies:
            dependency.update()

    def resolve(self, dependencies = None):
        logging.info('# Resolving versions')
        specs = [dependency.resolved_spec for dependency in self.dependencies]
        cartfile_resolve_path = self.root_path / "Cartfile.resolved"
        specs = [unicode(spec) for spec in specs]
        cartfile_resolve_path.open("w").write("\n".join(specs) + "\n")

    def checkout(self):
        pass

    def build(self, configuration = None, platform = None, only_dependencies = None):
        for dependency in self.dependencies:
            if only_dependencies:
                if dependency.name not in only_dependencies:
                    continue
            logging.info("# Building {}".format(dependency))
            dependency.build(configuration, platform)


class Specification(object):

    def __init__(self, spec):
        """
        >>> Specification('github "foo/bar"').spec
        'github "foo/bar"'
        >>> Specification('github "foo/bar" "master"').version
        "master"
        >>> Specification('github "foo/bar" "master"').origin
        'github "foo/bar"'
        >>> Specification('github "foo/bar" "master"').spec
        'github "foo/bar" "master"'
        >>> Specification('github "foo/bar" >= 1.0').spec
        'github "foo/bar" >= 1.0'
        >>> Specification('github "schwa/SwiftUtilities" "jwight/swift2"').name
        'SwiftUtilities'
        >>> Specification('github "schwa/SwiftUtilities" "jwight/swift2"').version
        "jwight/swift2"
        """

        match = re.match(r'^(github\s+"([^/]+/(.+?))")(?:\s+(.+)?)?', spec)
        if not match:
            raise Exception("Bad spec {}".format(spec))

        self.origin = match.group(1)
        self.remote_url = "git@github.com:{}.git".format(match.group(2))
        self.name = match.group(3)
        self.version = SpecVersion(match.group(4)) if match.group(4) else None

    def __repr__(self):
        return self.spec

    @property
    def spec(self):
        return self.origin + (" {}".format(self.version) if self.version else "")



class SpecVersion:
    def __init__(self, string):
        """
        >>> SpecVersion('"master"')
        "master"
        >>> SpecVersion('>= 1.0')
        >= 1.0
        >>> SpecVersion('<= 1.0')
        <= 1.0
        """
        #self.string = string
        self.type = None
        self.branch = None
        self.tag = None

        match = re.match(r'"(.+)"', string)
        if match:
            self.type = "branch"
            self.branch = match.group(1)
            return
        match = re.match(r'>= (.+)', string)
        if match:
            self.type = "gte"
            self.tag = match.group(1)
        match = re.match(r'<= (.+)', string)
        if match:
            self.type = "lte"
            self.tag = match.group(1)



    def __repr__(self):
        if self.type == "branch":
            return '"{}"'.format(self.branch)
        elif self.type == "gte":
            return ">= {}".format(self.tag)
        elif self.type == "lte":
            return "<= {}".format(self.tag)




class Dependency(object):

    def __init__(self, punic, spec):
        self.punic = punic
        self.spec = Specification(spec)
        self.name = self.spec.name
        self.version = None

        self.repo_path = self.punic.scratch_directory / self.name

        self.repo = None
        if self.repo_path.exists:
            self.repo = pygit2.Repository(str(self.repo_path))

    def __repr__(self):
        return "Dependency({})".format(self.spec)

    def update(self):
        if not self.repo_path.exists():
            with cwd(str(self.repo_path.parent)):
                logging.info("# Cloning: {}".format(self.spec))
                command = "git clone --recursive '{}'".format(self.spec.remote_url)
                command = shlex.split(command)
                self.repo = pygit2.Repository(str(self.repo_path))
        else:
            with cwd(str(self.repo_path)):
                logging.info("# Fetching: {}".format(self.spec))
                command = "git fetch"
                command = shlex.split(command)
                subprocess.check_output(command)
        self.repo = pygit2.Repository(str(self.repo_path))
        versions = sorted(self.versions)
        if not versions:
            raise Exception("No tags")
        self.version = versions[-1]
        # # Check out latest tag

        if self.spec.version.type == "branch":
            branch = "origin/{}".format(self.spec.version.branch)
            branch = self.repo.lookup_branch(branch, pygit2.GIT_BRANCH_REMOTE)
            self.repo.checkout(branch)
        else:
            self.repo.checkout("refs/tags/{}".format(self.version.raw))


    @property
    def versions(self):
        # Produce a list of all tags as Version objects
        regex = re.compile('^refs/tags/(.+)')
        # TODO: Double regex
        versions = [SemanticVersion(regex.match(ref).group(1)) for ref in self.repo.listall_references() if regex.match(ref)]
        return versions

    @property
    def project(self):
        project_name = "{}.xcodeproj".format(self.name)
        if (self.repo_path / project_name).exists():
            project = Project(self.repo_path / project_name)
        else:
            # Find first project!
            # TODO: Lame
            project_path = list(self.repo_path.glob("**/*.xcodeproj"))[0]
            project = Project(project_path)

        return project

    @property
    def resolved_spec(self):

        head = self.repo.lookup_reference('HEAD').resolve()
        version = head.get_object().oid

        spec = '{} "{}"'.format(self.spec.origin, version)

        return Specification(spec)

    def build(self, configuration = None, platform = None):
        project = self.project
        framework_targets = [target for target in project.targets if target.product_type == "com.apple.package-type.wrapper.framework"]
        for target in framework_targets:

            platform_name = target.build_settings["PLATFORM_NAME"]
            platform_nickname = { "iphoneos": "iOS", "macosx": "Mac"}[platform_name]

            if platform and platform_nickname != platform:
                return

            logging.info("# Building {}".format(target))

            # TODO: Should be unique per repo/version.
            symroot = self.punic.scratch_directory / "builds"

            build = Build(target, symroot, configuration)
            result = build.run()

            output_path = self.punic.build_path / platform_nickname / result.name
            if output_path.exists():
                shutil.rmtree(str(output_path))

            shutil.copytree(str(result), str(output_path), symlinks=True)

