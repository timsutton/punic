__author__ = 'schwa'
__all__ = ['SemanticVersion', 'Specification', 'Platform', 'Tag', 'ProjectIdentifier',
           'VersionOperator', 'VersionPredicate']

import re

from flufl.enum import Enum

class Tag(object):
    def __init__(self, string):
        self.tag = string
        self.semantic_version = SemanticVersion.string(self.tag)

    def __repr__(self):
        return str(self.semantic_version)

    def __cmp__(self, other):
        return cmp(self.semantic_version, other.semantic_version)

    def __hash__(self):
        return hash(self.semantic_version)


# TODO: Doesn't support full semvar.org spec
class SemanticVersion(object):
    @classmethod
    def is_semantic(cls, s):
        match = re.match('(?:v)?(\d+)(?:\.(\d+)(?:\.(\d+))?)?', s)
        return True if match else False

    def __init__(self, major, minor, revision):
        self.major = major
        self.minor = minor
        self.revision = revision

    @property
    def value(self):
        # TODO: Lazy
        return self.major * 1000000 + self.minor * 1000 + self.revision

    @property
    def components(self):
        return self.major, self.minor, self.revision

    def __repr__(self):
        return '{}.{}.{}'.format(*self.components)

    def __cmp__(self, other):
        # TODO: Lazy
        return cmp(self.value, other.value)

    def __hash__(self):
        return hash(self.value)

    @classmethod
    def string(cls, s):
        match = re.match('(?:v)?(\d+)(?:\.(\d+)(?:\.(\d+))?)?', s)
        if not match:
            raise Exception('"{}" not a semantic version.'.format(s))
        groups = match.groups()
        major = int(groups[0])
        minor = int(groups[1]) if groups[1] else 0
        revision = int(groups[2]) if groups[2] else 0
        return SemanticVersion(major=major, minor=minor, revision=revision)

    @property
    def next_major(self):
        return SemanticVersion(major=self.major + 1, minor=0, revision=0)


class Specification(object):
    def __init__(self, identifier, predicate):
        self.identifier = identifier
        self.predicate = predicate
        self.raw_string = None

    @classmethod
    def cartfile_string(cls, string):
        """Foo bar
        >>> Specification.cartfile_string('github 'foo/bar'').spec
        'github 'foo/bar''
        >>> Specification.cartfile_string('github 'foo/bar' 'master'').version
        'master'
        >>> Specification.cartfile_string('github 'foo/bar' 'master'').origin
        'github 'foo/bar''
        >>> Specification.cartfile_string('github 'foo/bar' 'master'').spec
        'github 'foo/bar' 'master''
        >>> Specification.cartfile_string('github 'foo/bar' >= 1.0').spec
        'github 'foo/bar' >= 1.0'
        >>> Specification.cartfile_string('github 'schwa/SwiftUtilities' 'jwight/swift2'').name
        'SwiftUtilities'
        >>> Specification.cartfile_string('github 'schwa/SwiftUtilities' 'jwight/swift2'').version
        'jwight/swift2'
        """

        match = re.match(r'^(github\s+"(([^/]+)/(.+?))")(?:\s+(.+)?)?', string)
        if not match:
            raise Exception('Bad spec {}'.format(string))

        remote_url = 'git@github.com:{}.git'.format(match.group(2))
        team_name = match.group(3)
        project_name = match.group(4)

        identifier = ProjectIdentifier(team_name=team_name, project_name=project_name, remote_url=remote_url)
        predicate = VersionPredicate(match.group(5))
        specification = Specification(identifier = identifier, predicate = predicate)
        specification.raw_string = string

        return specification

    def __repr__(self):
        return 'github "{identifier}" {predicate}'.format(**self.__dict__)


class ProjectIdentifier(object):
    def __init__(self, team_name=None, project_name=None, remote_url=None):
        self.team_name = team_name
        self.project_name = project_name
        self.remote_url = remote_url

        if not team_name:
            self.identifier = self.project_name
        else:
            self.identifier = "{}/{}".format(self.team_name, self.project_name)

    def __repr__(self):
        return self.identifier

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __lt__(self, other):
        return self.identifier < other.identifier

    def __hash__(self):
        return hash(self.identifier)


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
        'master'
        >>> VersionPredicate('>= 1.0')
        >= 1.0
        >>> VersionPredicate('~= 1.0')
        ~= 1.0
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
        for platform in cls.all:
            if platform.nickname.lower() == nickname.lower():
                return platform
        return None

Platform.all = [
    Platform(name = 'iOS', nickname = 'iOS', sdks = ['iphoneos', 'iphonesimulator'], output_directory_name = 'iOS'),
    Platform(name = 'macOS', nickname = 'Mac', sdks = ['macosx'], output_directory_name = 'Mac'),
    # TODO add watchos and tvos
]
