#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint

class UniPrinter(pprint.PrettyPrinter):
    """Pretty print lists and dicts containing unicode properly."""
    def pprint(self, object):
        if isinstance(object, str):
            unesc = unicode(object, 'unicode-escape')
        elif isinstance(object, unicode):
            unesc = unicode(object.encode('unicode-escape').\
                replace('\\\\u', '\\u'), 'unicode-escape')
        else:
            unesc = unicode(str(self.pformat(object)), 'unicode-escape')
        print unesc

# Usage:
# pp = UniPrinter(indent=4)
# pp.pprint(list)
