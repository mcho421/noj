#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from datetime import datetime
import os
import re
import json
import shutil
from sqlalchemy.sql import and_, select, func, bindparam
from anki import Collection
from pyparsing import *
from textwrap import dedent
from noj.misc.uni_printer import UniPrinter
from noj.model import (
    models,
    db,
    db_constants,
)
from noj.tools.japanese_parser import JapaneseParser
import noj.tools.entry_unformatter as uf
from noj.importers.abstract_importer import (
    AbstractCorpusImporterVisitor,
    UpdateImporterDecorator, 
    IntoKnownImporterDecorator,
)

from noj.model.models import Session
import pdb

__version__ = '1.0.0a'

pp = UniPrinter(indent=4)

soundRegexps = ["(?i)(\[sound:(?P<fname>[^]]+)\])"]
imgRegexps = [
    # src element quoted case
    "(?i)(<img[^>]* src=(?P<str>[\"'])(?P<fname>[^>]+?)(?P=str)[^>]*>)",
    # unquoted case
    "(?i)(<img[^>]* src=(?!['\"])(?P<fname>[^ >]+)[^>]*?>)",
]
regexps = soundRegexps + imgRegexps

class AnkiWalker(object):
    """Traverses an Anki deck while taking a visitor."""
    def __init__(self, collection_path, deck_name, lib_name=None,
                 expression_field=u'Expression', meaning_field=u'Meaning',
                 sound_field=None, image_field=None):
        super(AnkiWalker, self).__init__()
        self.collection_path = collection_path
        self.deck_name = deck_name
        self.lib_name = lib_name or (u'Anki Deck ' + deck_name)
        self.expression_field = expression_field
        self.meaning_field = meaning_field
        self.sound_field = sound_field
        self.image_field = image_field
        self.col = None
        self.ids = None
        self.media_dir = None

    def __len__(self):
        if self.ids is None:
            self.load_collection()
        return len(self.ids)

    def load_collection(self):
        self.col = Collection(self.collection_path, lock=False)
        self.ids = self.col.findNotes("\"deck:" + self.deck_name + "\" is:review")
        self.media_dir = re.sub("(?i)\.(anki2)$", ".media", self.col.path)

    def import_generator(self, visitor):
        """Imports the anki deck into the database.

        Session must be commited after done."""
        if self.ids is None:
            self.load_collection()

        visitor.visit_collection(self.col)
        visitor.visit_library(self.lib_name)
        visitor.visit_library_date(datetime.now().date().isoformat())
        visitor.visit_finish_library()

        for i, note_id in enumerate(self.ids):  # Loop over all notes in deck
            self._usage_example_accept(note_id, visitor)
            yield i

        visitor.visit_finish()

    def _usage_example_accept(self, note_id, visitor):
        # Get or create
        note = self.col.getNote(note_id)
        keys = note.keys()


        if self.expression_field in keys:
            expression = note.__getitem__(self.expression_field)

            visitor.visit_usage_example('UNKNOWN')
            visitor.visit_expression(expression)

            if self.meaning_field is not None and self.meaning_field in keys:
                meaning    = note.__getitem__(self.meaning_field)
                visitor.visit_meaning(meaning)

            self._media_accept(note, keys, visitor)

            visitor.visit_finish_usage_example(None)

    def _media_accept(self, note, keys, visitor):
        if self.sound_field is not None and self.sound_field in keys:
            sound_text = note.__getitem__(self.sound_field) # maybe use getattr(note, self.sound_field)
            for sound_re in soundRegexps:
                m = re.match(sound_re, sound_text)
                if m:
                    sound_candidate = m.group('fname')
                    if not re.match("(https?|ftp)://", sound_candidate.lower()):
                        sound = sound_candidate
                        visitor.visit_sound(sound)
                        break

        if self.image_field is not None and self.image_field in keys:
            image_text = note.__getitem__(self.image_field)
            for img_re in imgRegexps:
                m = re.match(img_re, image_text)
                if m:
                    image_candidate = m.group('fname')
                    if not re.match("(https?|ftp)://", image_candidate.lower()):
                        image = image_candidate
                        visitor.visit_image(image)
                        break

    def _get_media_folder_path(self):
        if self.ids is None:
            self.load_collection()
        return unicode(re.sub("(?i)\.(anki2)$", ".media", self.col.path))

class AnkiImporterVisitor(AbstractCorpusImporterVisitor):
    """Imports Anki deck using visitor pattern."""
    def __init__(self, session, parser, pm):
        super(AnkiImporterVisitor, self).__init__(session, parser)
        self.pm = pm
        self.media_dir = None

    def get_import_version(self):
        return __version__

    def visit_collection(self, col):
        self.media_dir = re.sub("(?i)\.(anki2)$", ".media", col.path)

    def _copy_media(self, ue_obj):
        if ue_obj.sound is not None:
            file_path = os.path.join(self.media_dir, ue_obj.sound)
            dest_path = os.path.join(self.pm.media_path(), ue_obj.sound)
            try:
                with open(file_path):
                    shutil.copyfile(file_path, dest_path)
            except IOError:
               pass
        if ue_obj.image is not None:
            file_path = os.path.join(self.media_dir, ue_obj.image)
            dest_path = os.path.join(self.pm.media_path(), ue_obj.image)
            try:
                with open(file_path):
                    shutil.copyfile(file_path, dest_path)
            except IOError:
               pass


def create_anki_sync_visitor(session, parser, pm):
    importer = AnkiImporterVisitor(session, parser, pm)
    importer = UpdateImporterDecorator(importer)
    importer = IntoKnownImporterDecorator(importer)
    return importer

def main():
    from sqlalchemy import create_engine
    from noj import init_db
    from noj.model.profiles import ProfileManager
    from noj.tools.check_platform import isWin, isMac
    pm = ProfileManager()
    engine = create_engine('sqlite:///../../test.sqlite', echo=False)
    # engine = create_engine(pm.database_connect_string(), echo=False)
    init_db(engine)
    if isWin:
        collection_path = 'C:\Users\Mathew\Documents\Anki\User 1\collection.anki2'
    else:
        collection_path = '/Users/mathew/Documents/Anki/User 1/collection.anki2'

    import progressbar as pb
    widgets = ['Importing: ', pb.Percentage(), ' ', pb.Bar(),
               ' ', pb.Timer(), ' ']

    session = Session()
    # importer = AnkiWalker(collection_path, 'Japanese', 
    #                         expression_field='Expression', meaning_field='Meaning')
    importer = AnkiWalker(collection_path, 'Core 2000 Japanese Vocabulary',
        expression_field='Sentence - Kanji', meaning_field='Sentence - English',
        sound_field='Sentence - Audio')
    parser = JapaneseParser()
    visitor = create_anki_sync_visitor(session, parser, pm)
    print importer._get_media_folder_path()

    pbar = pb.ProgressBar(widgets=widgets, maxval=len(importer)).start()
    for i in importer.import_generator(visitor):
        pbar.update(i)

    session.commit()
    session.close()
    pbar.finish()

if __name__ == '__main__':
    main()

