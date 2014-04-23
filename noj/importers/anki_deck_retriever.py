#!/usr/bin/env python
## -*- coding: utf-8 -*-
import sys
import os
from anki import Collection
from anki_importer import AnkiImporter

isMac = sys.platform.startswith("darwin")
isWin = sys.platform.startswith("win32")

class AnkiDeckRetriever(object):
    """Retrieves Anki2 decks"""

    def __init__(self, collection_path, lock=False):
        super(AnkiDeckRetriever, self).__init__()
        self.collection_path = collection_path
        self.col = Collection(collection_path, lock)
        self.expression_field = u"Expression"
        self.meaning_field = None
        self.deck_name = None
        self.lib_name = None

    @staticmethod
    def default_base():
        if isWin:
            import win32com.client
            objShell = win32com.client.Dispatch("WScript.Shell")
            d = objShell.SpecialFolders("MyDocuments")
            return os.path.join(d, "Anki")
        elif isMac:
            return os.path.expanduser("~/Documents/Anki")
        else:
            return os.path.expanduser("~/Anki")

    def get_deck_names(self):
        return sorted(self.col.decks.allNames())

    def get_fields(self):
        f_list = list()
        for m in self.col.models.all():
            f_list.extend(self.col.models.fieldNames(m))
        return sorted(list(set(f_list)))

    def set_deck_name(self, deck_name):
        self.deck_name = deck_name

    def set_lib_name(self, lib_name):
        self.lib_name = lib_name

    def set_expression_field(self, expression_field):
        self.expression_field = expression_field

    def set_meaning_field(self, meaning_field):
        self.meaning_field = meaning_field

    def construct_anki_importer(self):
        if self.collection_path is None:
            raise Exception("collection_path cannot be None")
        if self.deck_name is None:
            raise Exception("deck_name cannot be None")
        if self.expression_field is None:
            raise Exception("expression_field cannot be None")

        lib_name = self.lib_name or (u'Anki Deck ' + self.deck_name)

        # TODO: out of date
        return AnkiImporter(self.collection_path, self.deck_name, lib_name, 
                        self.expression_field, self.meaning_field)

def main():
    print AnkiDeckRetriever.default_base()
    collection_path = 'C:\Users\Mathew\Documents\Anki\User 1\collection.anki2'
    # col = get_collection(collection_path)
    # print get_deck_names(col)
    # print get_fields(col)
    anki_ret = AnkiDeckRetriever(collection_path)
    print anki_ret.get_deck_names()
    print anki_ret.get_fields()
    anki_ret.set_deck_name(u"Japanese")
    print anki_ret.construct_anki_importer()

if __name__ == '__main__':
    main()