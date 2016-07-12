__all__ = ['Repository', 'Revision']

import affirm

from flufl.enum import Enum
import logging
import contextlib

from memoize import mproperty

from punic.utilities import *
from punic.basic_types import *
from punic.runner import *
from punic.config import *
from punic.errors import *

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
            result = runner.run2('git tag')
            tags = result.stdout.read().split('\n')
            tags = [Revision(repository = self, revision = tag, revision_type = Revision.Type.tag) for tag in tags if SemanticVersion.is_semantic(tag)]
            return sorted(tags)

    def rev_parse(self, s):
        # type: (str) -> str
        with self.work_directory():
            return runner.run('git rev-parse {}'.format(s)).strip()

    def checkout(self, revision):
        # type: (str)
        logging.debug('# Checking out {} @ revision {}'.format(self, revision))
        with self.work_directory():
            runner.run('git checkout {}'.format(revision))

    def fetch(self):
        if not self.path.exists():
            with work_directory(str(self.path.parent)):
                logging.debug('# Cloning: {}'.format(self))
                runner.run('git clone --recursive "{}"'.format(self.identifier.remote_url))
        else:
            with self.work_directory():
                logging.debug('# Fetching: {}'.format(self))
                runner.run('git fetch')

    def specifications_for_revision(self, revision):
        # type: (str) -> [Specification]

        # logging.debug('Getting cartfile from revision {} of {})'.format(revision, self))

        if revision in self.specifications_cache:
            return self.specifications_cache[revision]
        elif revision == None and self == self.punic.root_project:
            cartfile = Cartfile()
            cartfile.read(self.path / "Cartfile")
            specifications = cartfile.specifications
        else:
            with self.work_directory():
                result = runner.run2('git show {}:Cartfile'.format(revision))
                if result.return_code != 0:
                    specifications = []
                else:
                    data = result.stdout.read()
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


class Revision(object):

    always_use_is_ancestor = False

    class Type(Enum):
        tag = 'tag'
        other = 'other'

    def __init__(self, repository, revision, revision_type):
        self.repository = repository
        self.revision = revision
        self.revision_type = revision_type
        self.semantic_version = (SemanticVersion.string(self.revision) if self.revision_type == Revision.Type.tag else None)

    @mproperty
    def sha(self):
        with work_directory(self.repository.path):
            return runner.run('git rev-parse "{}"'.format(self.revision), echo = False).strip()

    def __repr__(self):
        return str(self.revision)

    def __cmp__(self, other):
        if self.semantic_version and other.semantic_version and Revision.always_use_is_ancestor == False:
            return cmp(self.semantic_version, other.semantic_version)
        else:
            with work_directory(self.repository.path):
                if self.sha == other.sha:
                    result = 0
                else:
                    result = 1 if runner.result('git merge-base --is-ancestor "{}" "{}"'.format(other.sha, self.sha)) else -1

                    # TODO: just because X is not ancestor of Y doesn't mean Y is an ancestor of X
                    # if result == -1:
                    #     assert runner.result('git merge-base --is-ancestor "{}" "{}"'.format(self, other))
                return result

    def __hash__(self):
        return hash(self.revision)
