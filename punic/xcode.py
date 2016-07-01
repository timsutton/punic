__author__ = 'schwa'
__all__ = ['XcodeProject', 'xcodebuild']

import re
import shlex
import tempfile
import logging

from pathlib2 import Path
from memoize import mproperty

from punic.runner import *

class XcodeProject(object):
    def __init__(self, punic, path, identifier):
        self.punic = punic
        self.path = path
        self.identifier = identifier

    @property
    def targets(self):
        return self.info[0]

    @property
    def configurations(self):
        return self.info[1]

    @property
    def schemes(self):
        return self.info[2]

    @mproperty
    def info(self):
        command = xcodebuild(project=self.path, command='-list')
        output = self.punic.runner.run(cache_key=self.identifier, command=command)
        targets, configurations, schemes = parse_info(output)
        return targets, configurations, schemes

    @mproperty
    def base_command(self):
        command = 'xcodebuild -project "{}"'.format(self.path.name)
        return shlex.split(command)

    def build_settings(self, scheme=None, target=None, configuration=None, sdk=None, arguments=None):
        if not arguments:
            arguments = dict()
        command = xcodebuild(project=self.path, command='-showBuildSettings', scheme=scheme, target=target,
                             configuration=configuration, sdk=sdk, arguments=arguments)
        output = self.punic.runner.run(cache_key=self.identifier, command=command)
        return parse_build_settings(output)

    def build(self, scheme=None, target=None, configuration=None, sdk=None, arguments=None, temp_symroot = False):

        if not arguments:
            arguments = dict()

        if temp_symroot:
            symroot = tempfile.mkdtemp()
            arguments['SYMROOT'] = symroot

        command = xcodebuild(project=self.path, command='build', scheme=scheme, target=target,
                             configuration=configuration, sdk=sdk, arguments=arguments)
        run(command, echo = self.punic.echo)

        build_settings = self.build_settings(scheme=scheme, target=target, configuration=configuration, sdk=sdk,
                                             arguments=arguments)

        return Path('{TARGET_BUILD_DIR}/{FULL_PRODUCT_NAME}/{EXECUTABLE_NAME}'.format(**build_settings))


########################################################################################################################

def xcodebuild(project, command, scheme=None, target=None, configuration=None, sdk=None, jobs=None, arguments=None):
    if not arguments:
        arguments = dict()

    command = ['/usr/bin/xcrun', 'xcodebuild'] \
              + ['-project', str(project)] \
              + (['-scheme', scheme] if scheme else []) \
              + (['-target', target] if target else []) \
              + (['-configuration', configuration] if configuration else []) \
              + (['-sdk', sdk] if sdk else []) \
              + (['-jobs', str(jobs)] if jobs else []) \
              + ['{}={}'.format(key, value) for key, value in arguments.items()] \
              + [command]
    return command


########################################################################################################################

def parse_info(string):
    lines = iter(string.splitlines())
    targets = []
    configurations = []
    schemes = []

    try:
        while True:
            line = lines.next()
            if re.match(r'^\s+Targets:$', line):
                while True:
                    line = lines.next()
                    match = re.match(r'        (.+)', line)
                    if not match:
                        break
                    else:
                        targets.append(match.group(1))
            if re.match(r'^\s+Build Configurations:$', line):
                while True:
                    line = lines.next()
                    match = re.match(r'        (.+)', line)
                    if not match:
                        break
                    else:
                        configurations.append(match.group(1))
            if re.match(r'^\s+Schemes:$', line):
                while True:
                    line = lines.next()
                    match = re.match(r'        (.+)', line)
                    if not match:
                        break
                    else:
                        schemes.append(match.group(1))

    except StopIteration:
        pass

    return targets, configurations, schemes


def parse_build_settings(string):
    lines = iter(string.splitlines())
    matches = (re.match(r'^    (.+) = (.+)$', line) for line in lines)
    matches = (match.groups() for match in matches if match)
    return dict(matches)
