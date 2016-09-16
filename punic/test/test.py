
__all__ = ['test']

from click.testing import CliRunner
from pathlib2 import Path

from punic.punic_cli import punic_cli
from punic.utilities import work_directory
from punic.runner import *

import punic.shshutil as shutil

import tempfile



def test():
    test_data_path = Path(__file__).parent / 'Examples/SwiftIO'

    items = ['Cartfile', 'Cartfile.resolved', 'punic.yaml']

    temp_dir = Path(tempfile.mkdtemp())

    with work_directory(temp_dir):
        for item in items:
            shutil.copy(test_data_path / item, temp_dir)

        runner = Runner()
        output = runner.check_run('punic update')

        assert (Path.cwd() / 'Carthage/Build/Mac/SwiftIO.framework').exists()
        assert (Path.cwd() / 'Carthage/Build/Mac/SwiftUtilities.framework').exists()
        assert (Path.cwd() / 'Carthage/Build/Mac/SwiftIO.dSYM').exists()
        assert (Path.cwd() / 'Carthage/Build/Mac/SwiftUtilities.dSYM').exists()
