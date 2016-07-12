from __future__ import division, absolute_import, print_function

class RepositoryNotClonedError(Exception):
    pass

class CartfileNotFound(Exception):
    def __init__(self, path):
        self.path = path

