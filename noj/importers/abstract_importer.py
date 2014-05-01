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
