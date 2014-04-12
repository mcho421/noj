#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
from noj.model.definition_tree import DefinitionTreeVisitorHTML

# TODO: maybe need a factory?

class DictionaryResult(object):
    """has libraries"""
    def __init__(self, count=None):
        super(DictionaryResult, self).__init__()
        self.result_dict = dict()
        self.count = count

    def add(self, library_result):
        self.result_dict.add(library_result)

    def __getitem__(self, i):
        return self.result_dict.__getitem__(i)

    def __setitem__(self, k, value):
        return self.result_dict.__setitem__(k, value)

    def __contains__(self, elt):
        return self.result_dict.__contains__(elt)

    def __unicode__(self):
        blocks = list()
        for lib, lib_res in self.result_dict.items():
            blocks.append(unicode(lib_res))
        return '\n\n'.join(blocks)

    def __str__(self):
        return unicode(self).encode('unicode-escape')

class LibraryResult(object):
    """has entries"""
    def __init__(self, library, count=None):
        super(LibraryResult, self).__init__()
        self.library = library
        self.result_dict = dict()
        self.count = count

    def add(self, entry_result):
        self.result_dict.add(entry_result)

    def __getitem__(self, i):
        return self.result_dict.__getitem__(i)

    def __setitem__(self, k, value):
        return self.result_dict.__setitem__(k, value)

    def __contains__(self, elt):
        return self.result_dict.__contains__(elt)

    def __unicode__(self):
        blocks = list()
        # blocks.append(unicode(self.library))
        blocks.append(unicode(self.library.breadcrumb_string()))
        for entry, entry_res in self.result_dict.items():
            subblocks = unicode(entry_res).split('\n')
            for sb in subblocks:
                blocks.append('  ' + sb)
        return '\n'.join(blocks)

    def __str__(self):
        return unicode(self).encode('unicode-escape')

class EntryResult(object):
    """has definitions"""
    def __init__(self, entry, count=None):
        super(EntryResult, self).__init__()
        self.entry = entry
        self.result_dict = dict()
        self.count = count

    def add(self, definition_result):
        self.result_dict.add(definition_result)

    def __getitem__(self, i):
        return self.result_dict.__getitem__(i)

    def __setitem__(self, k, value):
        return self.result_dict.__setitem__(k, value)

    def __contains__(self, elt):
        return self.result_dict.__contains__(elt)

    def __unicode__(self):
        blocks = list()
        blocks2 = list()
        # blocks.append(unicode(self.entry))
        blocks.append(unicode(self.entry.breadcrumb_string()))
        for definition, definition_res in self.result_dict.items():
            blocks2.append(unicode(definition_res))
        indented = ['  ' + s for s in '\n\n'.join(blocks2).split('\n')]
        blocks.extend(indented)
        return '\n'.join(blocks)

    def __str__(self):
        return unicode(self).encode('unicode-escape')

class DefinitionResult(object):
    """has ues"""
    def __init__(self, definition, count=None):
        super(DefinitionResult, self).__init__()
        self.definition = definition
        self.result_list = list()
        self.count = count

    def append(self, ue_result):
        self.result_list.append(ue_result)

    def get_count(self):
        return self.count

    def __iter__(self):
        return self.result_list.__iter__()

    def __getitem__(self, i):
        return self.result_list.__getitem__(i)

    def __len__(self):
        return self.result_list.__len__()

    def __unicode__(self):
        blocks = list()
        blocks2 = list()
        # blocks.append(unicode(self.definition))
        blocks.append(unicode(self.definition.breadcrumb_string()))
        for i, ue in enumerate(self.result_list):
            blocks2.append(unicode(ue))
        indented = ['  ' + s for s in '\n\n'.join(blocks2).split('\n')]
        blocks.extend(indented)
        return '\n'.join(blocks)

    def __str__(self):
        return unicode(self).encode('unicode-escape')

class EntryList(object):
    """docstring for EntryList"""
    def __init__(self):
        super(EntryList, self).__init__()
        self.result_list = list()

    def append(self, entry):
        self.result_list.append(entry)

    def __iter__(self):
        return self.result_list.__iter__()

    def __getitem__(self, i):
        return self.result_list.__getitem__(i)

    def __len__(self):
        return self.result_list.__len__()

    def __unicode__(self):
        blocks = list()
        for i, entry in enumerate(self.result_list):
            lib_s = entry.library.breadcrumb_string()
            entry_s = entry.breadcrumb_string()
            definition_list = list()
            for definition in entry.definitions:
                definition_list.append(definition.breadcrumb_string())
            blocks.append(entry_s + ' -- ' + lib_s + '\n' + '\n'.join(definition_list))
        return '\n\n'.join(blocks)

    def to_html(self):
        blocks = list()
        for i, entry in enumerate(self.result_list):
            lib_s = entry.library.breadcrumb_string()
            entry_s = u"<p><a href=\"{}\" id=\"entry\">{}</a>".format("somelink", entry.breadcrumb_string())
            definition_tree = entry.definition_tree()
            html_visitor = DefinitionTreeVisitorHTML()
            definition_tree.accept(html_visitor)
            blocks.append(entry_s + u'<br/>' + html_visitor.get_HTML())
        return '<p>'.join(blocks)

    def __str__(self):
        return unicode(self).encode('unicode-escape')
        

class UEResultList(object):
    def __init__(self, count=None):
        super(UEResultList, self).__init__()
        self.result_list = list()
        self.count = count

    def append(self, ue_result):
        self.result_list.append(ue_result)

    def get_count(self):
        return self.count

    def __iter__(self):
        return self.result_list.__iter__()

    def __getitem__(self, i):
        return self.result_list.__getitem__(i)

    def __len__(self):
        return self.result_list.__len__()

    def __unicode__(self):
        blocks = list()
        for i, ue in enumerate(self.result_list):
            blocks.append(unicode(ue))
        return '\n\n'.join(blocks)

    def __str__(self):
        return unicode(self).encode('unicode-escape')

class UEResult(object):
    def __init__(self, search_word, usage_example, definition=None, entry=None):
        super(UEResult, self).__init__()
        self.search_word = search_word
        self.usage_example = usage_example
        self.definition = definition
        self.entry = entry

    def get_expression_score(self):
        return self.usage_example.get_n_score()

    def get_definition_score(self):
        pass # TODO

    def get_usage_example_id(self):
        return self.usage_example.id

    def get_expression(self):
        return self.usage_example.expression.expression

    def get_expression_id(self):
        return self.usage_example.expression.id

    def get_meaning(self):
        return self.usage_example.meaning

    def get_library_list(self):
        libraries = self._get_library_objs()
        return [lib.breadcrumb_string() for lib in libraries]

    def get_library_id_list(self):
        libraries = self._get_library_objs()
        return [lib.id for lib in libraries]

    def get_entry_list(self):
        entries = self._get_entry_objs()
        return [e.breadcrumb_string() for e in entries]

    def get_entry_id_list(self):
        entries = self._get_entry_objs()
        return [e.id for e in entries]

    def get_definition_list(self):
        definitions = self._get_definition_objs()
        return [d.breadcrumb_string() for d in definitions]

    def get_definition_id_list(self):
        definitions = self._get_definition_objs()
        return [d.id for d in definitions]

    def get_image(self):
        return self.usage_example.image

    def get_sound(self):
        return self.usage_example.sound

    def _get_definition_objs(self):
        definitions = set()
        if self.definition is None:
            definition_assocs = self.usage_example.definition_assocs
            for da in definition_assocs:
                definitions.add(da.definition)
        else:
            definitions.add(self.definition)
        return definitions

    def _get_entry_objs(self):
        entries = set()
        if self.entry is None:
            definitions = self._get_definition_objs()
            for d in definitions:
                entries.add(d.entry)
        else:
            entries.add(self.entry)
        return entries

    def _get_library_objs(self):
        libraries = set()
        libraries.add(self.usage_example.library)
        if self.entry is None:
            entries = self._get_entry_objs()
            for e in entries:
                libraries.add(e.library)
        return libraries

    def _get_source_line(self):
        parts = list()

        libraries = self.get_library_list()
        if len(libraries) == 1:
            parts.append(libraries[0])
        else:
            parts.append("(Multiple libraries)")

        entries = self.get_entry_list()
        if len(entries) == 1:
            parts.append(entries[0])
        else:
            parts.append("(Multiple entries)")

        definitions = self.get_definition_list()
        if len(definitions) == 1:
            parts.append(definitions[0])
        else:
            parts.append("(Multiple definitions)")

        return u' → '.join(parts)

    def __unicode__(self):
        return u"{escore}\n{expr}\n{meaning}\n{source}".format(
            escore=self.get_expression_score(),
            expr=self.get_expression(),
            meaning=self.get_meaning(),
            source=self._get_source_line())

    def __str__(self):
        return unicode(self).encode('unicode-escape')




        
