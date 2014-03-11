#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO: maybe need a factory?

class DictionaryResult(object):
    """has libraries"""
    def __init__(self):
        super(EntryResultTree, self).__init__()
        self.result_list = list()

    def append(self, library_result):
        self.result_list.append(library_result)

class LibraryResult(object):
    """has entries"""
    def __init__(self, library):
        super(LibraryResult, self).__init__()
        self.library = library
        self.result_list = list()

    def append(self, entry_result):
        self.result_list.append(entry_result)

class EntryResult(object):
    """has definitions"""
    def __init__(self, entry):
        super(EntryResult, self).__init__()
        self.entry = entry
        self.result_list = list()

    def append(self, definition_result):
        self.result_list.append(definition_result)

class DefinitionResult(object):
    """has ues"""
    def __init__(self, definition):
        super(DefinitionResult, self).__init__()
        self.definition = definition
        self.result_list = list()

    def append(self, ue_result):
        self.result_list.append(ue_result)

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




        
