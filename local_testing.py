from punic.cli import main

import sys
import os
import shlex

os.chdir('/Users/schwa/Desktop/3dr-Site-Scan-iOS')

sys.argv = shlex.split('punic --verbose --echo update --no-fetch')

main()

