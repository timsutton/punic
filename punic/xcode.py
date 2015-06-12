__author__ = 'schwa'
__all__ = ["Project", "Target", "Build"]

import re
import shlex
import subprocess
import tempfile

from pathlib import Path
from utilities import *

class Project(object):

    def __init__(self, path):
        self.path = path

        command = "xcodebuild -project '{}' -list".format(self.path.name)
        command = shlex.split(command)
        with cwd(str(self.path.parent)):
            result = subprocess.check_output(command, stderr=subprocess.PIPE)

            lines = iter(result.splitlines())

            targets = []
            configurations = []
            schemes = []

            try:
                while True:
                    line = lines.next()
                    if re.match(r"^\s+Targets:$", line):
                        while True:
                            line = lines.next()
                            match = re.match(r"        (.+)", line)
                            if not match:
                                break
                            else:
                                targets.append(match.group(1))
                    if re.match(r"^\s+Build Configurations:$", line):
                        while True:
                            line = lines.next()
                            match = re.match(r"        (.+)", line)
                            if not match:
                                break
                            else:
                                configurations.append(match.group(1))
                    if re.match(r"^\s+Schemes:$", line):
                        while True:
                            line = lines.next()
                            match = re.match(r"        (.+)", line)
                            if not match:
                                break
                            else:
                                schemes.append(match.group(1))

            except StopIteration:
                pass

            self.targets = [Target(self, target) for target in targets]

class Target(object):
    def __init__(self, project, name):
        self.project = project
        self.name = name

    def __repr__(self):
        return "Target(\"{}\" ({}))".format(self.name, self.build_settings["PLATFORM_NAME"])

    @property
    def base_command(self):
        command = "xcodebuild -project '{}' -target '{}'".format(self.project.path.name, self.name)
        command = shlex.split(command)
        return command

    @property
    def build_settings(self):
        if not hasattr(self, "_build_settings"):
            self._build_settings = get_build_settings(self, self.base_command)
        return self._build_settings

    @property
    def product_type(self):
        return self.build_settings.get("PACKAGE_TYPE", None)

def get_build_settings(target, base_command):
    command = base_command + ["-showBuildSettings"]
    with cwd(str(target.project.path.parent)):
        result = subprocess.check_output(command, stderr = subprocess.PIPE)
        lines = iter(result.splitlines())
        matches = (re.match(r"^    (.+) = (.+)$", line) for line in lines)
        matches = (match.groups() for match in matches if match)
        return dict(matches)


class Build(object):
    def __init__(self, target, symroot = None, configuration = None):
        self.target = target
        self.symroot = symroot if symroot else tempfile.mkdtemp()
        self.configuration = configuration

    @property
    def base_command(self):
        return self.target.base_command + ["SYMROOT={}".format(self.symroot)]

    @property
    def build_settings(self):
        if not hasattr(self, "_build_settings"):
            self._build_settings = get_build_settings(self.target, self.base_command)
        return self._build_settings

    def run(self):
        command = self.base_command + ["build"]
        with cwd(str(self.target.project.path.parent)):
            try:
                result = subprocess.check_output(command, stderr = subprocess.STDOUT)
            except subprocess.CalledProcessError, ex:
                print "--------error------"
                print ex.cmd
                print ex.message
                print ex.returncode
                print ex.output
            return Path("{TARGET_BUILD_DIR}/{FULL_PRODUCT_NAME}".format(**self.build_settings))

