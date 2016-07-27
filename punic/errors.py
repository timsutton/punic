from __future__ import division, absolute_import, print_function

import contextlib

from punic.logger import logger


class RepositoryNotClonedError(Exception):
    pass


class CartfileNotFound(Exception):
    def __init__(self, path):
        self.path = path


class PunicRepresentableError(Exception):
    pass


class NoSuchRevision(Exception):
    def __init__(self, repository, revision):
        self.repository = repository
        self.revision = revision


@contextlib.contextmanager
def error_handling():
    try:
        yield
    except RepositoryNotClonedError:
        logger.error('Error: No locally cloned repository found. Did you neglect to run `punic fetch` first?')
        exit(-1)
    except CartfileNotFound as e:
        logger.error('<err>Error</err>: No Cartfile found at path: <ref>{}</ref>'.format(e.path))
        exit(-1)
    except NoSuchRevision as e:
        logger.error('<err>Error</err>: No such revision {} found in repository {}'.format(e.revision, e.repository))
        logger.error(
            'Are you sure you are using the latest bits? Try an explicit `punic fetch` or use `punic bootstrap` instead of `punic build`')
        exit(-1)
    except PunicRepresentableError as e:
        logger.error(e.message)
        exit(-1)
    except:
        raise
