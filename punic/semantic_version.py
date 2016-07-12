from __future__ import division, absolute_import, print_function

import re
from functools import total_ordering

__all__ = ['SemanticVersion']


# TODO: Doesn't support full http://semvar.org spec
@total_ordering
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

    def __ne__(self, other):
        return not self.__eq__(other)

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
