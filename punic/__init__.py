from __future__ import division, absolute_import, print_function

__version__ = '0.0.9'

import sys
from pathlib2 import Path
from .punic_cli import *
from .carthage_cli import *

def main():
    path = Path(sys.argv[0])
    if path.name in set(['carthage_punic']):
        carthage_cli()
    else:
        punic_cli()
