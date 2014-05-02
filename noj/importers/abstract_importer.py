#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc
from noj.model import (
    models,
    db,
    db_constants,
)


class AbstractImporterVisitor(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, session, parser):
        super(AbstractImporterVisitor, self).__init__()
        self.session = session
        self.parser = parser
        self.morpheme_cache = dict()

        self.lib_obj = None
        self.lib_id = None
        self.entry_obj = None
        self.entry_id = None
        self.eformat = None

    def get_import_version(self):
        return None

    def visit_library(self):
        self.lib_obj = models.Library(type_id=db_constants.LIB_TYPES_TO_ID['DICTIONARY'],
                                      import_version=self.get_import_version())
        self.lib_id = None

    def visit_library_name(self, name):
        self.lib_obj.name = name

    def visit_library_dump_version(self, dump_version):
        self.lib_obj.dump_version = dump_version

    def visit_library_convert_version(self, convert_version):
        self.lib_obj.convert_version = convert_version

    def visit_library_date(self, date):
        self.lib_obj.date = date

    def visit_library_extra(self, extra):
        self.lib_obj.extra = extra

    def visit_finish_library(self):
        self.lib_id = db.insert_orm(self.session, self.lib_obj)[0]

    def visit_entry(self):
        self.entry_obj = models.Entry(library_id=self.lib_id)
        self.entry_id = None

    def visit_entry_format(self, eformat):
        self.eformat = eformat
        eformat_id = db.insert(self.session, models.EntryFormat, name=self.eformat)[0]
        self.entry_obj.format_id = eformat_id

    def _import_expression(self, expression):
        expression_id, new = db.insert(self.session, models.Expression, 
                                       expression=expression)
        if new:
            morpheme_list = self._import_parse_morphemes(expression)
            if len(morpheme_list) > 0:
                for m in morpheme_list:
                    m['expression_id'] = expression_id
                db.insert_many(self.session, models.ExpressionConsistsOf, 
                               morpheme_list)

        return expression_id

    def _import_parse_morphemes(self, line):
        results = self.parser.parse(line or '')

        # For bulk inserting the morpheme-expression association tuples
        morpheme_list = list()  # list of dicts representing fields

        for m in results:
            # Insert or get morpheme, (morpheme, type_id) unique
            morpheme_key = (m.base, m.type_)
            if morpheme_key in self.morpheme_cache:
                morpheme_id = self.morpheme_cache[morpheme_key]
            else:
                morpheme_id, new_morpheme, morpheme = db.insert_get(self.session, 
                    models.Morpheme, morpheme=m.base, type_id=m.type_,
                    status_id=db_constants.MORPHEME_STATUSES_TO_ID['AUTO'])
                self.morpheme_cache[morpheme_key] = morpheme_id

            # Bulk insert later
            morpheme_list.append({'morpheme_id':morpheme_id,
                                  'position':m.position, 
                                  'word_length':m.length,
                                  'conjugation':m.morpheme,
                                  'reading':m.reading})

        return morpheme_list
