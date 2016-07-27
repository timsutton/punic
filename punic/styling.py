from __future__ import division, absolute_import, print_function

__all__ = ['styled']

# noinspection PyUnresolvedReferences
from six.moves.html_parser import HTMLParser
from blessings import Terminal


class MyHTMLParser(HTMLParser):
    term = Terminal()

    def __init__(self, styled):
        HTMLParser.__init__(self)

        self.s = ''
        self.styled = styled

        self.styles = {'err': MyHTMLParser.term.red, 'ref': MyHTMLParser.term.yellow, 'rev': MyHTMLParser.term.bold, 'cmd': MyHTMLParser.term.cyan + self.term.underline, # 'sub': term.cyan,
            'echo': MyHTMLParser.term.yellow,}

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
        self.s += MyHTMLParser.term.normal
        for style in set(self.style_stack):
            self.s += style


def styled(s, styled):
    parser = MyHTMLParser(styled=styled)
    parser.feed(s)
    return parser.s + (MyHTMLParser.term.normal if styled else '')

# '<head>***</head> Checkout out <title>SwiftLogging</title> at "<version>v1.0.1</version>"')
#
# # instantiate the parser and fed it some HTML
