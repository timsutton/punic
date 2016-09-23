from __future__ import division, absolute_import, print_function

__all__ = ['styled']

# noinspection PyUnresolvedReferences
from six.moves.html_parser import HTMLParser
from blessings import Terminal

term = Terminal()

default_styles = {
    'err': term.red,
    'ref': term.yellow,
    'rev': term.bold,
    'cmd': term.cyan + term.underline,  # 'sub': term.cyan,
    'echo': term.yellow,
}


class MyHTMLParser(HTMLParser):



    def __init__(self, styled, styles = None):
        HTMLParser.__init__(self)

        self.s = ''
        self.styled = styled

        self.styles = styles if styles else default_styles
        self.style_stack = []

    # noinspection PyUnusedLocal
    def handle_starttag(self, tag, attrs):
        if tag in self.styles:
            self.style_stack.append(self.styles[tag])

    def handle_endtag(self, tag):
        if tag in self.styles:
            self.style_stack.pop()

    def handle_data(self, data):
        if self.styled:
            self.apply()
        self.s += data

    def apply(self):
        self.s += term.normal
        for style in set(self.style_stack):
            self.s += style


def styled(s, styled = True, styles = None):
    parser = MyHTMLParser(styled=styled, styles = styles)
    parser.feed(s)
    return parser.s + (term.normal if styled else '')

# '<head>***</head> Checkout out <title>SwiftLogging</title> at "<version>v1.0.1</version>"')
#
# # instantiate the parser and fed it some HTML
