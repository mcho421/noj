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
from noj.importers.abstract_importer import AbstractImporterVisitor

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

        for i, note_id in enumerate(self.ids):  # Loop over all notes in deck
            self._usage_example_accept(note_id, visitor)
            yield i

        visitor.visit_finish()

    def _usage_example_accept(self, note_id, visitor):
        # Get or create
        note = self.col.getNote(note_id)
        keys = note.keys()

        visitor.visit_usage_example(note)

        if self.expression_field in keys:
            expression = note.__getitem__(self.expression_field)
            visitor.visit_expression(expression)

            if self.meaning_field is not None and self.meaning_field in keys:
                meaning    = note.__getitem__(self.meaning_field)
                visitor.visit_meaning(meaning)

            self._media_accept(note, keys, visitor)

        visitor.visit_finish_usage_example()

    def _media_accept(self, note, keys, visitor):
        if self.sound_field is not None and self.sound_field in keys:
            sound_text = note.__getitem__(self.sound_field)
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

class AnkiImporterVisitor(AbstractImporterVisitor):
    """Imports Anki deck using visitor pattern."""
    def __init__(self, session, parser, pm):
        super(AnkiImporterVisitor, self).__init__(session, parser)
        self.pm = pm
        self.media_dir = None
        self.lib_id = None
        self.ue_obj = None
        self.ue_list_id = db_constants.KNOWN_EXAMPLES_ID
        # To reduce morpheme lookups
        self.morpheme_cache = dict() # (morpheme-unicode, type_id) -> morpheme-id
        self.morpheme_count = dict() # morpheme-id -> absolute count

    def visit_collection(self, col):
        self.media_dir = re.sub("(?i)\.(anki2)$", ".media", col.path)

    def visit_library(self, lib_name):
        """Imports library into database.

        Performs an update or create operation when importing the library.
        Returns id.
        """
        # Update or create UE library
        query = self.session.query(models.Library).filter(models.Library.name==lib_name)
        lib_obj = query.first()
        if lib_obj is None:
            lib_obj = models.Library(type_id=db_constants.LIB_TYPES_TO_ID['CORPUS'])
            lib_obj.name = lib_name

        lib_obj.import_version = __version__
        lib_obj.date = datetime.now().date().isoformat()
        self.lib_id = db.insert_orm_or_replace(self.session, lib_obj)

    def visit_usage_example(self, note):
        self.ue_obj = None

    def visit_expression(self, expression):
        # Need to handle morpheme counts
        expression_id = self._import_expression(expression)
        # print 'expression id:', expression_id

        # Insert or get usage example, (expression_id, library_id) unique
        self.ue_obj = models.UsageExample(library_id=self.lib_id)

        ue_type = 'UNKNOWN'
        ue_type = ue_type.upper()
        ue_type_id = db.insert(self.session, models.UEType, name=ue_type)[0]
        self.ue_obj.type_id = ue_type_id
        self.ue_obj.expression_id = expression_id

    def visit_meaning(self, meaning):
        self.ue_obj.meaning = meaning

    def visit_sound(self, sound):
        self.ue_obj.sound = sound

    def visit_image(self, image):
        self.ue_obj.image = image

    def visit_finish_usage_example(self):
        if self.ue_obj is not None:
            usage_example_id, new = db.insert_orm(self.session, self.ue_obj)

            # copy the sound and image files if new
            if new:
                self._copy_media(self.ue_obj)

            # print 'usage example id:', usage_example_id

            # if its a new expression, should be able to short circuit
            self._stage_morpheme_counts(self.ue_obj.expression_id)

            # Insert usage example into usage example list, no need to retrieve tuple
            db.insert_many_core(self.session, models.ue_part_of_list, [{
                                'ue_list_id':self.ue_list_id,
                                'usage_example_id':usage_example_id}])


    def visit_finish(self):
        # Update counts
        morpheme_count_updater = models.Morpheme.__table__.\
            update().where(models.Morpheme.__table__.c.id==bindparam('m_id')).\
            values(expr_count=bindparam('new_count'))

        morpheme_count_tuples = list()
        for morpheme_id, count in self.morpheme_count.items():
            morpheme_count_tuples.append({'m_id':morpheme_id, 'new_count':count})
            
        if morpheme_count_tuples:
            self.session.execute(morpheme_count_updater, morpheme_count_tuples)

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

    def _stage_morpheme_counts(self, expression_id):
        # Only stages morphemes from new expressions to be inserted to the list
        # Note: this should be done before mapping the expression to the list
        usage_examples  = models.UsageExample.__table__
        expression_consists_of = models.ExpressionConsistsOf.__table__
        morphemes = models.Morpheme.__table__
        ue_part_of_list = models.ue_part_of_list

        # Count number of times expression appears in list
        s = select([func.count(usage_examples.c.id)], 
            from_obj=[usage_examples.join(ue_part_of_list)],
            whereclause=and_(ue_part_of_list.c.ue_list_id==self.ue_list_id,
                             usage_examples.c.expression_id==expression_id))
        num_same_expressions = self.session.execute(s).first()[0]

        # Increment counts if expression not in list
        if num_same_expressions == 0:
            s = select([morphemes], 
                from_obj=[expression_consists_of.join(morphemes)], 
                whereclause=expression_consists_of.c.expression_id==expression_id)
            for m in self.session.execute(s):
                if m.id in self.morpheme_count:
                    self.morpheme_count[m.id] += 1
                else:
                    self.morpheme_count[m.id] = (m.expr_count or 0) + 1
        

def main():
    from sqlalchemy import create_engine
    from noj import init_db
    from noj.model.profiles import ProfileManager
    from noj.tools.check_platform import isWin, isMac
    pm = ProfileManager()
    # engine = create_engine('sqlite:///../../test.sqlite', echo=False)
    engine = create_engine(pm.database_connect_string(), echo=False)
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
    visitor = AnkiImporterVisitor(session, parser, pm)
    print importer._get_media_folder_path()

    pbar = pb.ProgressBar(widgets=widgets, maxval=len(importer)).start()
    for i in importer.import_generator(visitor):
        pbar.update(i)

    session.commit()
    session.close()
    pbar.finish()

if __name__ == '__main__':
    main()

