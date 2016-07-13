from __future__ import division, absolute_import, print_function

__all__ = ['SemanticVersion']

import re
from functools import total_ordering


# TODO: Doesn't support full http://semvar.org spec
@total_ordering
class SemanticVersion(object):
    @classmethod
    def is_semantic(cls, s):
        """
        >>> SemanticVersion.is_semantic("1.0")
        True
        >>> SemanticVersion.is_semantic("x.0")
        False
        """
        # type: (str) -> bool
        match = re.match('(?:v)?(\d+)(?:\.(\d+)(?:\.(\d+))?)?', s)
        return True if match else False

    def __init__(self, major, minor, patch=None, identifiers=None):
        """
        >>> SemanticVersion(1, 0)
        1.0
        >>> SemanticVersion(1, 0, 0)
        1.0
        """
        self.major = major if major else 0
        self.minor = minor if minor else 0
        self.patch = patch if patch else 0
        self.identifiers = identifiers if identifiers else []

    @property
    def value(self):
        # TODO: Lazy
        return self.major * 1000000 + self.minor * 1000 + self.patch

    @property
    def _components(self):
        """
        >>> SemanticVersion(1, 2, 3)._components
        [1, 2, 3]
        """
        # TODO: using a tuple breaks code
        #        return (self.major, self.minor, self.patch)
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
        return self._components == other._components

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
        return self._components < other._components

    def __hash__(self):
        return hash(self.major * 1000000) ^ hash(self.minor * 10000) ^ hash(self.patch * 100)


    @classmethod
    def from_dict(cls, d):
        if set(d.keys()).issubset(set(['major', 'minor', 'micro', 'releaselevel', 'serial'])):
            return SemanticVersion(
                major = d.get('major'),
                minor = d.get('minor'),
                patch = d.get('micro')
            )
        else:
            raise Exception('Invalid dict')

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
        """
        >>> SemanticVersion.string('1.2').next_major
        2.0
        """
        # type: () -> SemanticVersion
        return SemanticVersion(major=self.major + 1, minor=0, patch=0)
