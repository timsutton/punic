__all__ = ['Repository', 'Revision']

import affirm

from flufl.enum import Enum
import re
import logging

import pygit2
from memoize import mproperty

from punic.utilities import *
from punic.basic_types import *
from punic.runner import *
from punic.config import *

class Repository(object):
    def __init__(self, punic, identifier, repo_path):
        self.punic = punic
        self.identifier = identifier
        self.path = repo_path

    def __repr__(self):
        return str(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __lt__(self, other):
        return self.identifier < other.identifier

    def __hash__(self):
        return hash(self.identifier)

    @mproperty
    def repo(self):
        if not self.path.exists():
            raise Exception("Not such path: {}".format(self.path))
        return pygit2.Repository(str(self.path))

    @mproperty
    def tags(self):
        """Return a list of Tag objects representing git tags. Only tags that are valid semantic versions are returned"""
        # type: () -> [Tag]
        refs = self.repo.listall_references()
        regex = re.compile(r'^refs/tags/(.+)')
        refs = [ref for ref in refs if regex.match(ref)]
        refs = [regex.match(ref).group(1) for ref in refs]
        tags = [Revision(repository = self, revision = ref, revision_type = Revision.Type.tag) for ref in refs if SemanticVersion.is_semantic(ref)]
        return sorted(tags)

    def checkout(self, revision):
        # type: (String)
        logging.debug('# Checking out {} @ revision {}'.format(self, revision))
        #rev = self.repo.revparse_single(revision)
        #self.repo.checkout_tree(rev, strategy=pygit2.GIT_CHECKOUT_FORCE)
        with work_directory(str(self.path)):
            runner.run('git checkout {}'.format(revision))

    def fetch(self):
        if not self.path.exists():
            with work_directory(str(self.path.parent)):
                logging.debug('# Cloning: {}'.format(self))
                runner.run('git clone --recursive "{}"'.format(self.identifier.remote_url))
        else:
            with work_directory(str(self.path)):
                logging.debug('# Fetching: {}'.format(self))
                runner.run('git fetch')

    def specifications_for_revision(self, revision):
        # type: (Revision) -> [Specification]

        # logging.debug('Getting cartfile from tag {} of {}'.format(tag, self))

        if revision == None and self == self.punic.root_project:
            cartfile = Cartfile()
            cartfile.read(self.path / "Cartfile")
            return cartfile.specifications

        rev = self.repo.revparse_single(revision)
        if not hasattr(rev, 'tree'):
            rev = rev.get_object()
        if 'Cartfile' not in rev.tree:
            return []
        else:
#           runner.run('git show {}:Cartfile'.format(tag))
            cartfile = rev.tree['Cartfile']
            blob = self.repo[cartfile.id]
            cartfile = Cartfile()
            cartfile.read(blob.data)
            return cartfile.specifications

    def revisions_for_predicate(self, predicate):
        # type: (VersionPredicate) -> [Tag]
        return [tag for tag in self.tags if predicate.test(tag.semantic_version)]

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
