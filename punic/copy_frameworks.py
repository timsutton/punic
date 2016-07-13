from __future__ import division, absolute_import, print_function

__all__ = ['copy_frameworks_main']

import os
import re
import shutil
from pathlib2 import Path
from .runner import *
from .logger import *

def copy_frameworks_main():
    #
    sym_root = Path(os.environ['SYMROOT'])
    valid_architectures = set(os.environ['VALID_ARCHS'].split(' '))
    input_file_count = int(os.environ['SCRIPT_INPUT_FILE_COUNT'])
    input_files = [Path(os.environ.get('SCRIPT_INPUT_FILE_{}'.format(index))) for index in range(0, input_file_count)]
    expanded_identity = os.environ['EXPANDED_CODE_SIGN_IDENTITY_NAME']
    built_products_dir = Path(os.environ['BUILT_PRODUCTS_DIR'])
    frameworks_folder_path = os.environ['FRAMEWORKS_FOLDER_PATH']
    frameworks_path = built_products_dir / frameworks_folder_path
    code_signing_allowed = os.environ['CODE_SIGNING_ALLOWED'] == 'YES'

    for input_path in input_files:

        logger.info('Processing: "{}"'.format(input_path.name))

        # We don't modify the input frameworks but rather the ones in the built products directory
        output_path = frameworks_path / input_path.name

        framework_name = input_path.stem

        logger.info('\tCopying framework "{}" to "$SYMROOT/{}"'.format(framework_name, output_path.relative_to(sym_root)))
        if output_path.exists():
            shutil.rmtree(str(output_path))
        shutil.copytree(str(input_path), str(output_path))

        framework_path = output_path

        if not code_signing_allowed:
            logger.info('\tCode signing not allowed. Skipping')
            continue

        binary_path = framework_path / framework_name

        # Find out what architectures the framework has
        output = runner.check_call(['/usr/bin/xcrun', 'lipo', '-info', binary_path])
        match = re.match(r'^Architectures in the fat file: (.+) are: (.+)'.format(binary_path), output)
        assert match.groups()[0] == str(binary_path)
        architectures = set(match.groups()[1].strip().split(' '))
        logger.info('\tArchitectures: {}'.format(list(architectures)))

        # Produce a list of architectures that are not valid
        excluded_architectures = architectures.difference(valid_architectures)

        # Skip if all architectures are valid
        if not excluded_architectures:
            continue

        # For each invalid architecture strip it from framework
        for architecture in excluded_architectures:
            logger.info('\tStripping "{}" from "{}"'.format(architecture, framework_name))
            output = runner.check_call(['/usr/bin/xcrun', 'lipo', '-remove', architecture, '-output', binary_path, binary_path])

            # Resign framework
            logger.info('\tResigning "{}"/"{}" with "{}"'.format(framework_name, architecture, expanded_identity))

        logger.info('\tCode signing: "$SYMROOT/{}"'.format(binary_path.relative_to(sym_root)))

        # noinspection PyUnusedLocal
        result = runner.check_call(['/usr/bin/xcrun', 'codesign', '--force', '--sign', expanded_identity, '--preserve-metadata=identifier,entitlements', binary_path])

