from __future__ import division, absolute_import, print_function

__all__ = ['Repository', 'Revision']


from flufl.enum import Enum
import contextlib
import functools
import hashlib
import affirm
import six
from memoize import mproperty
from .utilities import *
from .runner import *
from .config import *
from .errors import *
from .logger import *
from .cartfile import *
from .semantic_version import *


class Repository(object):
    def __init__(self, punic, identifier, repo_path=None):
        self.punic = punic
        self.identifier = identifier
        if repo_path:
            self.path = repo_path
        else:
            url_hash = hashlib.md5(self.identifier.remote_url).hexdigest()
            self.path = punic.repo_cache_directory / "{}_{}".format(self.identifier.project_name, url_hash)

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
            try:
                runner.check_run('git checkout {}'.format(revision))
            except Exception:
                raise NoSuchRevision(repository=self, revision=revision)

    def fetch(self):

        if not self.path.exists():
            with work_directory(str(self.path.parent)):
                logger.debug('<sub>Cloning</sub>: <ref>{}</ref>'.format(self))

                url = self.identifier.remote_url
                import urlparse
                parsed_url = urlparse.urlparse(url)
                if parsed_url.scheme == 'file':
                    repo = parsed_url.path
                else:
                    repo = url

                runner.check_run('git clone --recursive "{}" {}'.format(repo, str(self.path)))
        else:
            with self.work_directory():
                logger.info('<sub>Fetching</sub>: <ref>{}</ref>'.format(self))
                runner.check_run('git fetch')

    def specifications_for_revision(self, revision):
        # type: (Revision) -> [Specification]

        assert not revision or isinstance(revision, Revision)

        # logger.debug('Getting cartfile from revision {} of {})'.format(revision, self))

        if revision in self.specifications_cache:
            return self.specifications_cache[revision]
        elif revision is None and self == self.punic.root_project:
            cartfile = Cartfile(overrides=config.repo_overrides)
            cartfile.read(self.path / 'Cartfile')
            specifications = cartfile.specifications
        else:
            with self.work_directory():
                result = runner.run('git show {}:Cartfile'.format(revision))
                if result.return_code != 0:
                    specifications = []
                else:
                    data = result.stdout
                    cartfile = Cartfile(overrides=config.repo_overrides)
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
        assert isinstance(repository, Repository)
        assert isinstance(revision, six.string_types)
#        assert isinstance(revision_type, Revision.Type) # TODO: This doesn't work.

        self.repository = repository
        self.revision = revision
        self.revision_type = revision_type
        self.semantic_version = (
            SemanticVersion.string(self.revision) if self.revision_type == Revision.Type.tag else None)

    @mproperty
    def sha(self):
        assert self.repository
        with work_directory(self.repository.path):
            output = runner.check_run('git rev-parse "{}"'.format(self.revision), echo=False)
            return output.strip()

    def __repr__(self):
        return str(self.revision)

    def __eq__(self, other):
        try:
            if self.semantic_version and other.semantic_version and not Revision.always_use_is_ancestor:
                return self.semantic_version == other.semantic_version
            else:
                return self.sha == other.sha
        except:
            logger.error(self.repository)
            raise

    # see: https://bugs.python.org/issue25732
    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        if self.semantic_version and other.semantic_version and not Revision.always_use_is_ancestor:
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
        # TODO: Should include repo too?
        return hash(self.revision)
