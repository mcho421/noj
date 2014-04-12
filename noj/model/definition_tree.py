#!/usr/bin/env python
import abc
from collections import defaultdict

class DefinitionTree(object):
    """Constructs tree for an entry's definitions"""
    def __init__(self, definitions):
        super(DefinitionTree, self).__init__()
        parent_child_map = defaultdict(list)
        for definition in definitions:
            pid = definition.parent_id
            parent_child_map[pid].append(definition)
        self.dtree = list()
        for d in parent_child_map[None]:
            self._append_definition_tree(d, self.dtree, parent_child_map)

    def _append_definition_tree(self, definition, parent_children, dmap):
        children = list()
        node = (definition, children)
        parent_children.append(node)
        for c in dmap[definition.id]:
            self._append_definition_tree(c, children, dmap)

    def accept(self, visitor, height=0):
        for definition, children in self.dtree:
            visitor.visit_definition(definition, height)
            self._accept_recurse(visitor, height+1, children)

    def _accept_recurse(self, visitor, height, dtree):
        for definition, children in dtree:
            visitor.visit_definition(definition, height)
            self._accept_recurse(visitor, height+1, children)


class DefinitionTreeVisitor:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def visit_definition(self, definition, height):
        pass
        
class DefinitionTreeVisitorHTML(object):
    def __init__(self):
        self.lines = list()

    def visit_definition(self, definition, height):
        d = definition.definition or '(No definition)'
        d = d.strip().replace('\n', ' ')
        def_s = u'&nbsp;'*height*4 + u"<font id=\"entry_definition\">(<a href=\"{}\"><font id=\"entry_definition_number\">{}</font></a>) {}".format("somelink", definition.number, d)
        self.lines.append(def_s)

    def get_HTML(self):
        return u'<br/>'.join(self.lines)        
