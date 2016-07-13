from __future__ import division, absolute_import, print_function

__all__ = ['Repository', 'Revision']

import affirm

from flufl.enum import Enum
import contextlib
import functools

from memoize import mproperty

from .utilities import *
from .basic_types import *
from .runner import *
from .config import *
from .errors import *
from .logger import *
from .cartfile import *

class Repository(object):
    def __init__(self, punic, identifier, repo_path):
        self.punic = punic
        self.identifier = identifier
        self.path = repo_path
        self.specifications_cache = dict()

    def __repr__(self):
        return str(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __lt__(self, other):
        return self.identifier < other.identifier

    def __hash__(self):
        return hash(self.identifier)

    @mproperty
    def tags(self):
        """Return a list of Tag objects representing git tags. Only tags that are valid semantic versions are returned"""
        # type: () -> [Tag]

        with self.work_directory():
            output = runner.check_run('git tag')
            tags = output.split('\n')
            tags = [Revision(repository=self, revision=tag, revision_type=Revision.Type.tag) for tag in tags if
                    SemanticVersion.is_semantic(tag)]
            return sorted(tags)

    def rev_parse(self, s):
        # type: (str) -> str
        with self.work_directory():
            output = runner.check_run('git rev-parse {}'.format(s))
            return output.strip()

    def checkout(self, revision):
        # type: (str)
        logger.debug('Checking out <ref>{}</ref> @ revision <rev>{}</rev>'.format(self, revision))
        with self.work_directory():
            runner.check_run('git checkout {}'.format(revision))

    def fetch(self):
        if not self.path.exists():
            with work_directory(str(self.path.parent)):
                logger.debug('<sub>Cloning</sub>: <ref>{}</ref>'.format(self))
                runner.check_run('git clone --recursive "{}"'.format(self.identifier.remote_url))
        else:
            with self.work_directory():
                logger.debug('<sub>Fetching</sub>: <ref>{}</ref>'.format(self))
                runner.check_run('git fetch')

    def specifications_for_revision(self, revision):
        # type: (str) -> [Specification]

        # logger.debug('Getting cartfile from revision {} of {})'.format(revision, self))

        if revision in self.specifications_cache:
            return self.specifications_cache[revision]
        elif revision is None and self == self.punic.root_project:
            cartfile = Cartfile()
            cartfile.read(self.path / "Cartfile")
            specifications = cartfile.specifications
        else:
            with self.work_directory():
                result = runner.run('git show {}:Cartfile'.format(revision))
                if result.return_code != 0:
                    specifications = []
                else:
                    data = result.stdout
                    cartfile = Cartfile()
                    cartfile.read(data)
                    specifications = cartfile.specifications

        self.specifications_cache[revision] = specifications
        return specifications

    def revisions_for_predicate(self, predicate):
        # type: (VersionPredicate) -> [Tag]
        return [tag for tag in self.tags if predicate.test(tag.semantic_version)]

    @contextlib.contextmanager
    def work_directory(self):
        if not self.path.exists():
            raise RepositoryNotClonedError()
        with work_directory(self.path):
            yield


########################################################################################################################


@functools.total_ordering
class Revision(object):
    always_use_is_ancestor = False

    class Type(Enum):
        tag = 'tag'
        other = 'other'

    def __init__(self, repository, revision, revision_type):
        self.repository = repository
        self.revision = revision
        self.revision_type = revision_type
        self.semantic_version = (
        SemanticVersion.string(self.revision) if self.revision_type == Revision.Type.tag else None)

    @mproperty
    def sha(self):
        with work_directory(self.repository.path):
            output = runner.check_run('git rev-parse "{}"'.format(self.revision), echo=False)
            return output.strip()

    def __repr__(self):
        return str(self.revision)

    def __eq__(self, other):
        if self.semantic_version and other.semantic_version and Revision.always_use_is_ancestor == False:
            return self.semantic_version == other.semantic_version
        else:
            return self.sha == other.sha

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if self.semantic_version and other.semantic_version and Revision.always_use_is_ancestor == False:
            return self.semantic_version < other.semantic_version
        else:
            with work_directory(self.repository.path):
                result = runner.run('git merge-base --is-ancestor "{}" "{}"'.format(other, self))
                if result.return_code == 0:
                    return False
                if result.return_code == 1:
                    return True
                else:
                    raise Exception('git merge-base returned {}'.format(result.return_code))

    def __hash__(self):
        return hash(self.revision)
