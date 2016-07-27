from __future__ import division, absolute_import, print_function

__all__ = ['version_check']

import requests
import punic
from .logger import *
from .semantic_version import *


def version_check(verbose=False, timeout=0.3, failure_is_an_option=True):
    try:
        log = logger.info if verbose else logger.debug

        log('<sub>Checking punic version...</sub>', prefix=not verbose)

        current_version = SemanticVersion.string(punic.__version__)
        # TODO: Is this the best URL?
        result = requests.get('https://raw.githubusercontent.com/schwa/punic/develop/VERSION', timeout=timeout)
        latest_version = SemanticVersion.string(result.text.strip())

        log(
            'Current version: <rev>{}</rev>, latest version: <rev>{}</rev>'.format(current_version, latest_version),
            prefix=not verbose)
        if current_version < latest_version:
            logger.warn("""You are using version <rev>{}</rev>, version <rev>{}</rev> is available.
            Use <echo>`pip install -U http://github.com/schwa/punic`</echo> to update to latest version.""".format(
                current_version, latest_version))
    # TODO: Duplicated code
    except requests.exceptions.ReadTimeout as e:
        logger.debug('<error>Failed to check versions')
        if not failure_is_an_option:
            raise e
    except requests.exceptions.ConnectTimeout as e:
        logger.debug('<error>Failed to check versions')
        if not failure_is_an_option:
            raise e
