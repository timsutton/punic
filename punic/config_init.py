from __future__ import division, absolute_import, print_function

__all__ = ['config_init']

import pureyaml
from pathlib2 import Path
from .basic_types import *
from .xcode import  *
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import (AutoSuggest, Suggestion)

class ListAutoSuggest(AutoSuggest):
    def __init__(self, items):
        self.items = items


    def get_suggestion(self, cli, buffer, document):

        # Consider only the last line for the suggestion.
        text = document.text.rsplit('\n', 1)[-1]

        # Only create a suggestion when this is not an empty line.
        if text.strip():
            # Find first matching line in history.
            for string in self.items:
                for line in reversed(string.splitlines()):
                    if line.startswith(text):
                        return Suggestion(line[len(text):])

def platform_nicknames():
    return sorted([p.nickname for p in Platform.all])

def _xcode_versions():
    Xcode.find_all()
    return sorted([unicode(version) for version in Xcode.all_xcodes.keys()])

def _prompt(s, items, default = None):
    items = [unicode(item) for item in items]
    # text = prompt(u'X: ', )
    # text = prompt(u'{}: '.format(s), auto_suggest = ListAutoSuggest(items), default = items[0])
    completer = WordCompleter(items, ignore_case=True)

    kwargs = {
        'completer': completer,
        'complete_while_typing': True,
    }

    if default:
        kwargs['default'] = unicode(default)

    text = prompt(u'{} ({}): '.format(s, u', '.join(items)), **kwargs)
    if not text:
        return None
    return text


def config_init(**kwargs):
    """Generate punic configuration file."""

    kwargs['xcode_version'] = None

    d = {
        'defaults': {},
    }

    configuration = _prompt("Configuration", ['Debug', 'Release'])
    if configuration:
        d['defaults']['configuration'] = configuration

    platform = _prompt("Platform", platform_nicknames())
    if platform:
        d['defaults']['platform'] = platform

    # xcode_version = _prompt("Xcode Version", _xcode_versions())
    # if xcode_version:
    #     d['defaults']['xcode_version'] = xcode_version

    s = pureyaml.dumps(d)
    print(s)
    if _prompt('Write config to `punic.yaml`', ['yes', 'no'], default = 'no') == 'yes':
        Path('punic.yaml').open('wb').write(s)
