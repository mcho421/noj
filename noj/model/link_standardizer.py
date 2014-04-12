#!/usr/bin/env python

def dictionary_search_link(dictionary, search_word=None):
    if search_word is None:
        return u'dictionary/{}'.format(dictionary.id)
    return u'dictionary/{}/{}'.format(dictionary.id, search_word)

def entry_link(entry, search_word=None):
    if search_word is None:
        return u'entry/{}'.format(entry.id)
    return u'entry/{}/{}'.format(entry.id, search_word)

def definition_link(definition, search_word=None):
    if search_word is None:
        return u'definition/{}'.format(definition.id)
    return u'definition/{}/{}'.format(definition.id, search_word)

def ues_via_expression_item_entries_link(idx):
    return u'uvexpr/{}/entries'.format(idx)

def ues_via_expression_item_definitions_link(idx):
    return u'uvexpr/{}/definitions'.format(idx)

def ues_via_entry_item_entries_link(idx):
    return u'uvent/{}/entries'.format(idx)

def ues_via_entry_item_definitions_link(idx):
    return u'uvent/{}/definitions'.format(idx)


