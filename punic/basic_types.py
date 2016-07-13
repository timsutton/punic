from __future__ import division, absolute_import, print_function

__all__ = ['Specification', 'Platform', 'ProjectIdentifier',
    'VersionOperator', 'VersionPredicate', 'parse_platforms']

import re
import urlparse
import functools

from pathlib2 import Path
from memoize import mproperty
from flufl.enum import Enum

from .logger import *


# TODO: Doesn't support full http://semvar.org spec
@functools.total_ordering
class SemanticVersion(object):
    @classmethod
    def is_semantic(cls, s):
        # type: (str) -> bool
        match = re.match('(?:v)?(\d+)(?:\.(\d+)(?:\.(\d+))?)?', s)
        return True if match else False

    def __init__(self, major, minor, patch=None, identifiers=None):
        self.major = major if major else 0
        self.minor = minor if minor else 0
        self.patch = patch if patch else 0
        self.identifiers = identifiers if identifiers else []

    @property
    def value(self):
        # TODO: Lazy
        return self.major * 1000000 + self.minor * 1000 + self.patch

    @property
    def components(self):
        return [self.major, self.minor, self.patch]

    def __repr__(self):
        components = [self.major, self.minor] + ([self.patch] if self.patch else [])
        components = [str(component) for component in components]
        return '.'.join(components)

    def __eq__(self, other):
        """
        >>> SemanticVersion.string('1') == SemanticVersion.string('1')
        True
        >>> SemanticVersion.string('1') == SemanticVersion.string('1.0')
        True
        >>> SemanticVersion.string('1') == SemanticVersion.string('1.0.0')
        True
        >>> SemanticVersion.string('1') != SemanticVersion.string('1')
        False
        """
        return self.components == other.components

    # see: https://bugs.python.org/issue25732
    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        """
        >>> SemanticVersion.string('1') < SemanticVersion.string('2')
        True
        >>> SemanticVersion.string('1') <= SemanticVersion.string('2')
        True
        >>> SemanticVersion.string('1.1') > SemanticVersion.string('1.0')
        True
        """
        return self.components < other.components

    def __hash__(self):
        return hash(self.major * 1000000) ^ hash(self.minor * 10000) ^ hash(self.patch * 100)

    @classmethod
    def string(cls, s):
        # type: (str) -> SemanticVersion
        """
        >>> SemanticVersion.string('1')
        1.0
        >>> SemanticVersion.string('1.2')
        1.2
        >>> SemanticVersion.string('1.2.3')
        1.2.3

        # >>> SemanticVersion.string('1.0-foo')
        # 1.0-foo
        """
        match = re.match('(?:v)?(\d+)(?:\.(\d+)(?:\.(\d+))?)?', s)
        if not match:
            raise Exception('"{}" not a semantic version.'.format(s))
        groups = match.groups()
        major = int(groups[0])
        minor = int(groups[1]) if groups[1] else None
        patch = int(groups[2]) if groups[2] else None
        return SemanticVersion(major=major, minor=minor, patch=patch)

    @property
    def next_major(self):
        # type: () -> SemanticVersion
        return SemanticVersion(major=self.major + 1, minor=0, patch=0)


class Specification(object):
    def __init__(self, identifier, predicate):
        self.identifier = identifier
        self.predicate = predicate
        self.raw_string = None

    @classmethod
    def cartfile_string(cls, string, overrides):
        # type: (str) -> Specification
        """
        >>> Specification.cartfile_string('github "foo/bar"')
        github "foo/bar"
        >>> Specification.cartfile_string('github "foo/bar" "master"').identifier
        foo/bar
        >>> Specification.cartfile_string('github "foo/bar" "master"').predicate
        "master"
        >>> Specification.cartfile_string('github "foo/bar" "master"')
        github "foo/bar" "master"
        >>> Specification.cartfile_string('github "foo/bar" >= 1.0').predicate
        >= 1.0
        >>> Specification.cartfile_string('github "ReactiveX/RxSwift" "some/branch"').identifier
        ReactiveX/RxSwift
        >>> Specification.cartfile_string('github "ReactiveX/RxSwift" "some/branch"').predicate
        "some/branch"
        >>> Specification.cartfile_string('file:///Users/example/Project').identifier
        file:///Users/example/Project
        >>> Specification.cartfile_string('file:///Users/example/Project').identifier.project_name
        'Project'
        """

        match = re.match(r'^(?P<address>github\s+"[^/]+/(?:.+?)")(?:\s+(?P<predicate>.+)?)?', string)
        if not match:
            match = re.match(r'^(?P<address>file:///.+)(?:\s+(?P<predicate>.+)?)?', string)
            if not match:
                raise Exception('Bad spec {}'.format(string))

        identifier = ProjectIdentifier.string(match.group('address'), overrides=overrides)
        predicate = VersionPredicate(match.group('predicate'))
        specification = Specification(identifier=identifier, predicate=predicate)
        specification.raw_string = string

        return specification

    def __repr__(self):
        return 'github "{identifier}" {predicate}'.format(**self.__dict__).strip()


class ProjectIdentifier(object):
    @classmethod
    def string(cls, string, overrides=None):
        # type: (str) -> ProjectIdentifier
        """
        >>> ProjectIdentifier.string('github "foo/bar"')
        foo/bar
        >>> ProjectIdentifier.string('github "foo/bar"').team_name
        'foo'
        >>> ProjectIdentifier.string('github "foo/bar"').project_name
        'bar'
        >>> ProjectIdentifier.string('file:///example')
        file:///example
        >>> ProjectIdentifier.string('file:///example').remote_url
        'file:///example'
        """

        match = re.match(r'^github\s+"(?P<team_name>.+)/(?P<project_name>.+)"', string)
        if match:
            team_name = match.group('team_name')
            project_name = match.group('project_name')
            remote_url = 'git@github.com:{}/{}.git'.format(team_name, project_name)
            return ProjectIdentifier(overrides=overrides, team_name=team_name, project_name=project_name,
                remote_url=remote_url)
        else:
            match = re.match(r'file:///.+', string)
            if not match:
                raise Exception('Bad project identifier: {}'.format(string))
            remote_url = match.group(0)

            path = Path(urlparse.urlparse(remote_url).path)
            project_name = path.name

            return ProjectIdentifier(overrides=overrides, project_name=project_name, remote_url=remote_url)

    def __init__(self, team_name=None, project_name=None, remote_url=None, overrides=None):
        self.team_name = team_name
        self.project_name = project_name
        self.remote_url = remote_url
        if overrides and self.project_name in overrides:
            override_url = overrides[self.project_name]
            logger.info('Overriding {} with git URL {}'.format(self.project_name, override_url))
            self.remote_url = override_url

    @mproperty
    def identifier(self):
        if self.team_name and self.project_name:
            return "{}/{}".format(self.team_name, self.project_name)
        elif self.remote_url:
            return self.remote_url
        else:
            return '<unnamed>'

    def __repr__(self):
        return self.identifier

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __lt__(self, other):
        return self.identifier < other.identifier

    def __hash__(self):
        return hash(self.identifier)

    def matches(self, name_filter=None):
        # type: ([str]) -> bool

        if not name_filter:
            return True

        if self.project_name in name_filter:
            return True

        return False


class VersionOperator(Enum):
    commitish = 'commit-ish'
    any = '<any>'
    greater_than_or_equals = '>='
    equals = '=='
    semantic_greater_than_or_equals = '~>'


class VersionPredicate(object):
    def __init__(self, string):
        """
        >>> VersionPredicate('"master"')
        "master"
        >>> VersionPredicate('>= 1.0')
        >= 1.0
        >>> VersionPredicate('~> 1.0')
        ~> 1.0
        >>> VersionPredicate('== 1.0')
        == 1.0
        """

        if not string:
            self.operator = VersionOperator.any
            self.value = None
        else:
            match = re.match(r'(?:(~>|>=|==|)\s+)?(?:"(.+)"|(.+))', string)
            if not match:
                raise Exception('No match for: {}'.format(string))

            operator = match.group(1)
            value = match.group(2) if match.group(2) else match.group(3)

            if operator == '==':
                self.operator = VersionOperator.equals
                self.value = SemanticVersion.string(value)
            elif operator == '>=':
                self.operator = VersionOperator.greater_than_or_equals
                self.value = SemanticVersion.string(value)
            elif operator == '~>':
                self.operator = VersionOperator.semantic_greater_than_or_equals
                self.value = SemanticVersion.string(value)
            else:
                self.operator = VersionOperator.commitish
                self.value = value

    def __repr__(self):
        if self.operator == VersionOperator.any:
            return ''
        if self.operator == VersionOperator.commitish:
            return '"{}"'.format(self.value)
        elif self.operator == VersionOperator.equals:
            return '== {}'.format(self.value)
        elif self.operator == VersionOperator.greater_than_or_equals:
            return '>= {}'.format(self.value)
        elif self.operator == VersionOperator.semantic_greater_than_or_equals:
            return '~> {}'.format(self.value)

    def test(self, version):
        # type: (SemanticVersion) -> bool
        if self.operator == VersionOperator.any:
            return True
        elif self.operator == VersionOperator.equals:
            return version == self.value
        elif self.operator == VersionOperator.greater_than_or_equals:
            return version >= self.value
        elif self.operator == VersionOperator.semantic_greater_than_or_equals:
            return self.value <= version <= self.value.next_major
        return False


class Platform(object):
    def __init__(self, name, nickname, sdks, output_directory_name):
        self.name = name
        self.nickname = nickname
        self.sdks = sdks
        self.output_directory_name = output_directory_name

    @classmethod
    def platform_for_nickname(cls, nickname):
        # type: (str) -> Platform
        for platform in cls.all:
            if platform.nickname.lower() == nickname.lower():
                return platform
        return None

    def __repr__(self):
        return self.nickname


Platform.all = [
    Platform(name='iOS', nickname='iOS', sdks=['iphoneos', 'iphonesimulator'], output_directory_name='iOS'),
    Platform(name='macOS', nickname='Mac', sdks=['macosx'], output_directory_name='Mac'),
    # TODO add watchos and tvos
]


def parse_platforms(s):
    # type: (str) -> [Platform]
    if not s:
        return Platform.all
    else:
        return [Platform.platform_for_nickname(platform.strip()) for platform in s.split(',')]
