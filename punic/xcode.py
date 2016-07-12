__author__ = 'Jonathan Wight <jwight@mac.com>'
__all__ = ['XcodeProject', 'xcodebuild', 'uuids_from_binary', 'BuildProduct']

import re
import shlex
import tempfile

from pathlib2 import Path
from memoize import mproperty

from punic.runner import *


class XcodeProject(object):
    def __init__(self, punic, path, identifier):
        self.punic = punic
        self.path = path
        self.identifier = identifier

        # os.environ['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'

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
        output = runner.run(cache_key=self.identifier, command=command)
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
        output = runner.run(cache_key=self.identifier, command=command)
        return parse_build_settings(output)

    def build(self, scheme=None, target=None, configuration=None, sdk=None, arguments=None, temp_symroot=False):

        if not arguments:
            arguments = dict()

        if temp_symroot:
            symroot = tempfile.mkdtemp()
            arguments['SYMROOT'] = symroot

        command = xcodebuild(project=self.path, command='build', scheme=scheme, target=target,
                             configuration=configuration, sdk=sdk, arguments=arguments)
        runner.run(command)

        build_settings = self.build_settings(scheme=scheme, target=target, configuration=configuration, sdk=sdk,
                                             arguments=arguments)

        return BuildProduct.build_settings(build_settings)


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


########################################################################################################################

class BuildProduct(object):
    @classmethod
    def build_settings(cls, build_settings):
        product = BuildProduct()
        product.build_settings = build_settings
        product.full_product_name = build_settings['FULL_PRODUCT_NAME']  # 'Example.framework'
        product.product_name = build_settings['PRODUCT_NAME']  # 'Example'
        product.executable_name = build_settings['EXECUTABLE_NAME']  # 'Example'
        product.target_build_dir = Path(build_settings[
                                            'TARGET_BUILD_DIR'])  # ~/Library/Developer/Xcode/DerivedData/Example-<random>/Build/Products/<configuration>-<sdk>
        return product

    @classmethod
    def string(cls, string):
        lines = iter(string.splitlines())
        matches = (re.match(r'^    (.+) = (.+)$', line) for line in lines)
        matches = (match.groups() for match in matches if match)
        build_settings = dict(matches)

        product = BuildProduct.build_settings(build_settings=build_settings)
        return product

    def __init__(self):
        self.build_settings = dict()
        self.full_product_name = None
        self.product_name = None
        self.executable_name = None
        self.target_build_dir = None

    @property
    def product_path(self):
        return self.target_build_dir / self.full_product_name

    @property
    def executable_path(self):
        return self.product_path / self.executable_name

    @property
    def uuids(self):
        return uuids_from_binary(self.executable_path)

    @property
    def bcsymbolmap_paths(self):
        paths = [self.target_build_dir / (uuid + '.bcsymbolmap') for uuid in self.uuids]
        paths = [path for path in paths if path.exists()]
        return paths

    @property
    def module_paths(self):
        modules_source_path = self.product_path / "Modules/{}.swiftmodule".format(self.executable_name)
        if not modules_source_path.exists():
            return []
        return list(modules_source_path.glob("*"))


########################################################################################################################

def parse_build_settings(string):
    lines = iter(string.splitlines())
    matches = (re.match(r'^    (.+) = (.+)$', line) for line in lines)
    matches = (match.groups() for match in matches if match)
    return dict(matches)


########################################################################################################################

def uuids_from_binary(path):
    command = ['/usr/bin/xcrun', 'dwarfdump', '--uuid', path]
    output = runner.run(command)
    lines = output.splitlines()
    matches = [re.match(r'^UUID: ([0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}) \((.+)\) (.+)$', line)
               for line in lines]
    uuids = [match.group(1) for match in matches]
    return uuids
