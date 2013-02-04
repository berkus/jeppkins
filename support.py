# Factor out all helper functions.

from HTMLParser import HTMLParser
import htmlentitydefs

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
# HELPER FUNCTIONS
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.result = [ ]

    def handle_data(self, d):
        self.result.append(d)

    def handle_charref(self, number):
        codepoint = int(number[1:], 16) if number[0] in (u'x', u'X') else int(number)
        self.result.append(unichr(codepoint))

    def handle_entityref(self, name):
        if name == 'apos':
	    codepoint = ord("'")
	else:
            codepoint = htmlentitydefs.name2codepoint[name]
        self.result.append(unichr(codepoint))

    def get_text(self):
        return u''.join(self.result)

# Strip html tags also converting entities.
def html_to_text(html):
    s = HTMLTextExtractor()
    s.feed(html)
    return s.get_text()
