from __future__ import division, absolute_import, print_function


class RepositoryNotClonedError(Exception):
    pass


class CartfileNotFound(Exception):
    def __init__(self, path):
        self.path = path


class NoSuchRevision(Exception):
    def __init__(self, repository, revision):
        self.repository = repository
        self.revision = revision
