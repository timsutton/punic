__all__ = ['styled']

from blessings import Terminal

term = Terminal()
from HTMLParser import HTMLParser

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)

        self.s = ''

        self.styles = {
            'head': term.blue,
            'title': term.bold,
            'version': term.bold,
            'command': term.red + term.bold,
        }

        self.style_stack = []

    def handle_starttag(self, tag, attrs):
        if tag in self.styles:
            self.style_stack.append(self.styles[tag])

    def handle_endtag(self, tag):
        if tag in self.styles:
            self.style_stack.pop()

    def handle_data(self, data):
        self.apply()
        self.s += data

    def apply(self):
        self.s += term.normal
        for style in set(self.style_stack):
            self.s += style

def styled(s):
    parser = MyHTMLParser()
    parser.feed(s)
    return parser.s + term.normal

# '<head>***</head> Checkout out <title>SwiftLogging</title> at "<version>v1.0.1</version>"')
#
# # instantiate the parser and fed it some HTML
