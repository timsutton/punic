from __future__ import division, absolute_import, print_function

__all__ = ['copy_frameworks_main']

import os
import re
from pathlib2 import Path
import logging

from .runner import *
from .xcode import uuids_from_binary
import punic.shshutil as shutil


def copy_frameworks_main():
    sym_root = Path(os.environ['SYMROOT'])
    valid_architectures = set(os.environ['VALID_ARCHS'].split(' '))
    input_file_count = int(os.environ['SCRIPT_INPUT_FILE_COUNT'])
    input_files = [Path(os.environ.get('SCRIPT_INPUT_FILE_{}'.format(index))) for index in range(0, input_file_count)]
    expanded_identity = os.environ['EXPANDED_CODE_SIGN_IDENTITY_NAME']
    built_products_dir = Path(os.environ['BUILT_PRODUCTS_DIR'])
    frameworks_folder_path = os.environ['FRAMEWORKS_FOLDER_PATH']
    frameworks_path = built_products_dir / frameworks_folder_path
    code_signing_allowed = os.environ['CODE_SIGNING_ALLOWED'] == 'YES'
    enable_bitcode = os.environ['ENABLE_BITCODE'] == 'YES'
    project_dir = Path(os.environ['PROJECT_DIR'])
    platform_display_name = os.environ['PLATFORM_DISPLAY_NAME']
    punic_builds_dir = project_dir / 'Carthage' / 'Build' / platform_display_name
    action = os.environ['ACTION']

    for input_path in input_files:

        logging.info('Processing: "{}"'.format(input_path.name))

        # We don't modify the input frameworks but rather the ones in the built products directory
        output_path = frameworks_path / input_path.name

        framework_name = input_path.stem

        logging.info('\tCopying framework "{}" to "$SYMROOT/{}"'.format(framework_name, output_path.relative_to(sym_root)))
        if output_path.exists():
            shutil.rmtree(output_path)

        def ignore(src, names):
            src = Path(src)
            if src.suffix == ".framework":
                return ['Headers', 'PrivateHeaders', 'Modules']
            else:
                return []

        shutil.copytree(input_path, output_path, symlinks=True, ignore = ignore)

        framework_path = output_path

        binary_path = framework_path / framework_name

        if code_signing_allowed:
            # Find out what architectures the framework has
            output = runner.check_call(['/usr/bin/xcrun', 'lipo', '-info', binary_path])
            match = re.match(r'^Architectures in the fat file: (.+) are: (.+)'.format(binary_path), output)
            assert match.groups()[0] == str(binary_path)
            architectures = set(match.groups()[1].strip().split(' '))
            logging.info('\tArchitectures: {}'.format(list(architectures)))

            # Produce a list of architectures that are not valid
            excluded_architectures = architectures.difference(valid_architectures)

            # Skip if all architectures are valid
            if not excluded_architectures:
                continue

            # For each invalid architecture strip it from framework
            for architecture in excluded_architectures:
                logging.info('\tStripping "{}" from "{}"'.format(architecture, framework_name))
                output = runner.check_call(['/usr/bin/xcrun', 'lipo', '-remove', architecture, '-output', binary_path, binary_path])

                # Resign framework
                logging.info('\tResigning "{}"/"{}" with "{}"'.format(framework_name, architecture, expanded_identity))

            logging.info('\tCode signing: "$SYMROOT/{}"'.format(binary_path.relative_to(sym_root)))

            # noinspection PyUnusedLocal
            result = runner.check_call(['/usr/bin/xcrun', 'codesign', '--force', '--sign', expanded_identity, '--preserve-metadata=identifier,entitlements', binary_path])
        else:
            logging.info('\tCode signing not allowed. Skipping.')

        if action == 'install':
            uuids = uuids_from_binary(binary_path)

            # Copy dSYM files from $PROJECT_DIRCarthage/Build to $BUILT_PRODUCTS_DIR
            dsym_path = input_path.parent / (binary_path.name + '.dSYM')

            if dsym_path.exists():

                dsym_output_path = built_products_dir / dsym_path.name

                logging.info('\tCopying "$PROJECT_DIR/{}" to "$BUILT_PRODUCTS_DIR"'.format(dsym_path.relative_to(project_dir)))
                if dsym_output_path.exists():
                    shutil.rmtree(dsym_output_path)
                shutil.copytree(dsym_path, dsym_output_path, symlinks=True)

            # Copy bcsymbolmap files from $PROJECT_DIRCarthage/Build to $BUILT_PRODUCTS_DIR
            if enable_bitcode:
                for uuid in uuids:
                    bcsymbolmap_path = punic_builds_dir / (uuid + '.bcsymbolmap')
                    logging.info('\tCopying "$PROJECT_DIR/{}" to "$BUILT_PRODUCTS_DIR"'.format(bcsymbolmap_path.relative_to(project_dir)))
                    shutil.copy(bcsymbolmap_path, built_products_dir)
