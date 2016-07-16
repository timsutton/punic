from __future__ import division, absolute_import, print_function

__all__ = ['Xcode', 'XcodeProject', 'uuids_from_binary', 'XcodeBuildProduct', 'XcodeBuildArguments']

import re
import affirm
from pathlib2 import Path
from memoize import mproperty
import six
from .runner import *
from .logger import *
from .semantic_version import *


class Xcode(object):
    all_xcodes = None
    default_xcode = None

    @classmethod
    def default(cls):
        if not Xcode.default_xcode:
            Xcode.find_all()
        return Xcode.default_xcode

    @classmethod
    def find_all(cls):
        output = runner.check_run(
            '/usr/bin/mdfind \'kMDItemCFBundleIdentifier="com.apple.dt.Xcode" and kMDItemContentType="com.apple.application-bundle"\'')
        xcodes = [Xcode(Path(path)) for path in output.strip().split("\n")]
        Xcode.all_xcodes = dict([(xcode.version, xcode) for xcode in xcodes])
        default_developer_dir_path = Path(runner.check_run(['xcode-select', '-p']).strip())
        Xcode.default_xcode = [xcode for version, xcode in Xcode.all_xcodes.items() if
            xcode.developer_dir_path == default_developer_dir_path][0]

    def __init__(self, path):
        self.path = path
        self.developer_dir_path = self.path / 'Contents/Developer'

    @mproperty
    def version(self):
        output = self.check_call(['xcodebuild', '-version'], env={'DEVELOPER_DIR': str(self.developer_dir_path)})
        match = re.match(r'^Xcode (?P<version>.+)\nBuild version (?P<build>.+)', output)
        return SemanticVersion.string(match.groupdict()['version'])

    # noinspection PyMethodMayBeStatic
    def call(self, command, **kwargs):
        command = runner.convert_args(command)
        command = ['/usr/bin/xcrun'] + command
        result = runner.run(command, **kwargs)
        return result

    # noinspection PyMethodMayBeStatic
    def check_call(self, command, **kwargs):
        command = runner.convert_args(command)
        command = ['/usr/bin/xcrun'] + command
        result = runner.check_run(command, **kwargs)
        return result

    def __repr__(self):
        return '{} ({})'.format(self.path, self.version)


########################################################################################################################

class XcodeProject(object):
    def __init__(self, punic, xcode, path, identifier):
        self.punic = punic
        self.xcode = xcode if xcode else Xcode.default()
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
        arguments = XcodeBuildArguments()
        arguments.project = self.path
        output = self.check_call(subcommand='-list', cache_key=self.identifier)
        targets, configurations, schemes = parse_info(output)
        return targets, configurations, schemes

    def build_settings(self, arguments):
        # type: (XcodeBuildArguments) -> dict()
        output = self.check_call(subcommand='-showBuildSettings', arguments=arguments, cache_key=self.identifier)
        return parse_build_settings(output)

    def build(self, arguments):
        # type: (XcodeBuildArguments) -> dict()
        try:
            self.check_call(subcommand='build', arguments = arguments)
        except CalledProcessError as e:
            logger.error('<err>Error</err>: Failed to build - result code <echo>{}</echo>'.format(e.returncode))
            logger.error('Command: <echo>{}</echo>'.format(e.cmd))
            logger.error(e.output)
            exit(e.returncode)

        build_settings = self.build_settings(arguments=arguments)
        assert(build_settings)

        return XcodeBuildProduct.build_settings(build_settings)

    def check_call(self, subcommand, arguments = None, **kwargs):
        # type: (str, XcodeBuildArguments) -> [str]
        assert not arguments or isinstance(arguments, XcodeBuildArguments)
        arguments = arguments.to_list() if arguments else []
        command = ['xcodebuild', '-project', self.path] + arguments + [subcommand]
        return self.xcode.check_call(command, **kwargs)


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

class XcodeBuildArguments(object):
    def __init__(self, scheme = None, target = None, configuration = None, sdk = None, jobs = None, derived_data_path = None, arguments = None):
        self.scheme = scheme
        self.target = target
        self.configuration = configuration
        self.sdk = sdk
        self.jobs = jobs
        self.derived_data_path = derived_data_path
        self.arguments = arguments

    def __repr__(self):
        return 'XcodeBuildArguments({})'.format(self.__dict__)

    def to_list(self):
        # type: () -> [Any]
        parts = []
        parts += ['-scheme', self.scheme] if self.scheme else []
        parts += ['-target', self.target] if self.target else []
        parts += ['-configuration', self.configuration] if self.configuration else []
        parts += ['-sdk', self.sdk] if self.sdk else []
        parts += ['-jobs', self.jobs] if self.jobs else []
        parts += ['-derivedDataPath', self.derived_data_path] if self.derived_data_path else []
        parts += (['{}={}'.format(key, value) for key, value in self.arguments.items()]) if self.arguments else []
        return parts


########################################################################################################################


class XcodeBuildProduct(object):
    @classmethod
    def build_settings(cls, build_settings):
        product = XcodeBuildProduct()
        product.build_settings = build_settings
        product.full_product_name = build_settings['FULL_PRODUCT_NAME']  # 'Example.framework'
        product.product_name = build_settings['PRODUCT_NAME']  # 'Example'
        product.executable_name = build_settings['EXECUTABLE_NAME']  # 'Example'
        product.target_build_dir = Path(build_settings['TARGET_BUILD_DIR'])  # ~/Library/Developer/Xcode/DerivedData/Example-<random>/Build/Products/<configuration>-<sdk>
        return product

    def __repr__(self):
        return 'BuildProduct({})'.format(self.__dict__)

    @classmethod
    def string(cls, string):
        lines = iter(string.splitlines())
        matches = (re.match(r'^    (.+) = (.+)$', line) for line in lines)
        matches = (match.groups() for match in matches if match)
        build_settings = dict(matches)

        product = XcodeBuildProduct.build_settings(build_settings=build_settings)
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
    output = runner.check_run(command)
    lines = output.splitlines()
    matches = [re.match(r'^UUID: ([0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}) \((.+)\) (.+)$', line)
        for line in lines]
    uuids = [match.group(1) for match in matches]
    return uuids
