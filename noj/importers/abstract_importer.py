#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc
import json
from noj.model import (
    models,
    db,
    db_constants,
)
import noj.tools.entry_unformatter as uf
from sqlalchemy.sql import and_, select, func, bindparam


class AbstractImporterVisitor(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, session, parser):
        super(AbstractImporterVisitor, self).__init__()
        self.session = session
        self.parser = parser
        self.morpheme_cache = dict() # (morpheme-unicode, type_id) -> morpheme-id

        self.lib_obj = None
        self.lib_id = None
        self.definition_ues = None
        self.ue_obj = None

    def get_import_version(self):
        return None

    def visit_library(self, name):
        self.lib_obj = models.Library(type_id=db_constants.LIB_TYPES_TO_ID['DICTIONARY'],
                                      import_version=self.get_import_version(),
                                      name=name)
        self.lib_id = None

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

    def visit_usage_example(self, ue_type):
        self.ue_obj = models.UsageExample(library_id=self.lib_id)

        ue_type = ue_type.upper()
        ue_type_id = db.insert(self.session, models.UEType, name=ue_type)[0]
        self.ue_obj.type_id = ue_type_id

    def visit_expression(self, expression):
        expression_id = self._import_expression(expression)
        self.ue_obj.expression_id = expression_id

    def visit_ue_reading(self, reading):
        self.ue_obj.reading = reading

    def visit_meaning(self, meaning):
        self.ue_obj.meaning = meaning

    def visit_sound(self, sound):
        self.ue_obj.sound = sound

    def visit_image(self, image):
        self.ue_obj.image = image

    def visit_ue_extra(self, extra):
        self.ue_obj.extra = extra

    def visit_ue_validated(self, is_validated):
        self.ue_obj.is_validated = is_validated

    @abc.abstractmethod
    def visit_finish_usage_example(self, number):
        pass

    def visit_finish(self):
        pass

    def _copy_media(self, ue_obj):
        pass

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

class AbstractDictionaryImporterVisitor(AbstractImporterVisitor):
    __metaclass__ = abc.ABCMeta

    def __init__(self, session, parser):
        super(AbstractDictionaryImporterVisitor, self).__init__(session, parser)
        self.entry_obj = None
        self.entry_id = None
        self.eformat = None
        self.last_kana_text = None
        self.def_obj = None
        self.def_id = None
        self.def_id_stack = list()
        self.ue_id = None

    def visit_entry(self):
        # TODO: entry number not set
        self.entry_obj = models.Entry(library_id=self.lib_id)
        self.entry_id = None
        self.last_kana_text = None

    def visit_entry_format(self, eformat):
        self.eformat = eformat
        eformat_id = db.insert(self.session, models.EntryFormat, name=self.eformat)[0]
        self.entry_obj.format_id = eformat_id

    def visit_kana_raw_list(self, kana_raw_list):
        self.entry_obj.kana_raw = json.dumps(kana_raw_list)

    def visit_kanji_raw_list(self, kanji_raw_list):
        self.entry_obj.kanji_raw = json.dumps(kanji_raw_list)

    def visit_accent(self, accent):
        self.entry_obj.accent = accent

    def visit_entry_extra(self, extra):
        self.entry_obj.extra = extra

    def visit_construct_entry(self):
        self.entry_id = db.insert_orm(self.session, self.entry_obj)[0]

    def visit_kana_list(self, kana_list):
        entry_kana = list()
        if self.eformat == 'J-J1':
            for i, kana_text in enumerate(kana_list):
                kana_id = db.insert(self.session, models.Morpheme, 
                    morpheme=uf.unformat_jj1_kana(kana_text),
                    type_id=db_constants.MORPHEME_TYPES_TO_ID['KANA_ENTRY'],
                    status_id=db_constants.MORPHEME_STATUSES_TO_ID['AUTO'])[0]
                entry_kana.append({'entry_id':self.entry_id, 'kana_id':kana_id, 'number':i+1})
                self.last_kana_text = kana_text
        else:
            for i, kana_text in enumerate(kana_list):
                kana_id = db.insert(self.session, models.Morpheme, morpheme=kana_text,
                    type_id=db_constants.MORPHEME_TYPES_TO_ID['KANA_ENTRY'],
                    status_id=db_constants.MORPHEME_STATUSES_TO_ID['AUTO'])[0]
                entry_kana.append({'entry_id':self.entry_id, 'kana_id':kana_id, 'number':i+1})
        db.insert_many(self.session, models.EntryHasKana, entry_kana)

    def visit_kanji_list(self, kanji_list):
        entry_kanji = list()
        if self.eformat == 'J-J1':
            for i, kanji_text in enumerate(kanji_list):
                kanji_id = db.insert(self.session, models.Morpheme, 
                    morpheme=uf.unformat_jj1_kanji(kanji_text, self.last_kana_text), # TODO: assert(last_kana_text is not None)
                    type_id=db_constants.MORPHEME_TYPES_TO_ID['KANJI_ENTRY'],
                    status_id=db_constants.MORPHEME_STATUSES_TO_ID['AUTO'])[0]
                entry_kanji.append({'entry_id':self.entry_id, 'kanji_id':kanji_id, 'number':i+1})
        else:
            for i, kanji_text in enumerate(kanji_list):
                kanji_id = db.insert(self.session, models.Morpheme, morpheme=kanji_text,
                    type_id=db_constants.MORPHEME_TYPES_TO_ID['KANJI_ENTRY'],
                    status_id=db_constants.MORPHEME_STATUSES_TO_ID['AUTO'])[0]
                entry_kanji.append({'entry_id':self.entry_id, 'kanji_id':kanji_id, 'number':i+1})
        db.insert_many(self.session, models.EntryHasKanji, entry_kanji)

    def visit_definition(self, number):
        self.def_id_stack.append(self.def_id)
        parent_id = self.def_id
        self.def_id = None
        self.definition_ues = list()

        self.def_obj = models.Definition(entry_id=self.entry_id, number=number)

        if parent_id is not None:
            self.def_obj.parent_id = parent_id

    def visit_definition_group(self, group):
        self.def_obj.group = group

    def visit_definition_text(self, text):
        self.def_obj.definition = text

    def visit_definition_extra(self, extra):
        self.def_obj.extra = extra

    def visit_construct_definition(self):
        self.def_id = db.insert_orm(self.session, self.def_obj)[0]
        if self.eformat == 'J-J1':
            self._import_definition_assocs(self.def_obj.definition, self.def_id)

    def visit_finish_definition(self):
        self.def_id = self.def_id_stack.pop()

    def visit_finish_definition_ues(self):
        db.insert_many(self.session, models.DefinitionHasUEs, self.definition_ues)

    def _import_definition_assocs(self, def_text, def_id):
        if def_text is not None:
            morpheme_list = self._import_parse_morphemes(def_text)
            if len(morpheme_list) > 0:
                for m in morpheme_list:
                    m['definition_id'] = def_id
                db.insert_many(self.session, models.DefinitionConsistsOf, 
                               morpheme_list)

    def visit_finish_usage_example(self, number):
        if self.ue_obj is not None:
            self.ue_id, new = db.insert_orm(self.session, self.ue_obj)

            self.definition_ues.append({'usage_example_id': self.ue_id, 'definition_id': self.def_id,
                                   'number': number})

            if new:
                self._copy_media(self.ue_obj)

class AbstractCorpusImporterVisitor(AbstractImporterVisitor):
    __metaclass__ = abc.ABCMeta

    def __init__(self, session, parser):
        super(AbstractCorpusImporterVisitor, self).__init__(session, parser)

    def visit_finish_usage_example(self, number):
        # number parameter is not used in corpus import
        if self.ue_obj is not None:
            self.ue_id, new = db.insert_orm(self.session, self.ue_obj)

            # copy the sound and image files if new
            if new:
                self._copy_media(self.ue_obj)

# For corpus only
class UpdateImporterDecorator(object):
    """docstring for UpdateImporterDecorator"""
    def __init__(self, importer):
        super(UpdateImporterDecorator, self).__init__()
        self.importer = importer

    def __getattr__(self, name):
        return getattr(self.importer, name)

    def visit_library(self, lib_name):
        """Imports library into database.

        Performs an update or create operation when importing the library.
        Returns id.
        """
        # Update or create UE library
        query = self.session.query(models.Library).filter(models.Library.name==lib_name)
        self.importer.lib_obj = query.first()
        if self.importer.lib_obj is None:
            self.importer.visit_library(lib_name)

        self.importer.lib_obj.import_version = self.importer.get_import_version()

    def visit_finish_library(self):
        self.importer.lib_id = db.insert_orm_or_replace(self.importer.session, self.importer.lib_obj)

# generalize to arbitrary list
class IntoKnownImporterDecorator(object):
    """docstring for IntoKnownImporterDecorator"""
    def __init__(self, importer):
        super(IntoKnownImporterDecorator, self).__init__()
        self.importer = importer
        self.ue_list_id = db_constants.KNOWN_EXAMPLES_ID
        # To reduce morpheme lookups
        self.morpheme_count = dict() # morpheme-id -> absolute count

    def __getattr__(self, name):
        return getattr(self.importer, name)

    def visit_finish_usage_example(self, number):
        # number is not used in corpus import
        if self.importer.ue_obj is not None: # TODO: get rid of this if statement
            self.importer.visit_finish_usage_example(number)

            # if its a new expression, should be able to short circuit
            self._stage_morpheme_counts(self.importer.ue_obj.expression_id)

            # Insert usage example into usage example list, no need to retrieve tuple
            db.insert_many_core(self.importer.session, models.ue_part_of_list, [{
                                'ue_list_id':self.ue_list_id,
                                'usage_example_id':self.importer.ue_id}])

    def visit_finish(self):
        self.importer.visit_finish()

        # Update counts
        morpheme_count_updater = models.Morpheme.__table__.\
            update().where(models.Morpheme.__table__.c.id==bindparam('m_id')).\
            values(expr_count=bindparam('new_count'))

        morpheme_count_tuples = list()
        for morpheme_id, count in self.morpheme_count.items():
            morpheme_count_tuples.append({'m_id':morpheme_id, 'new_count':count})
            
        if morpheme_count_tuples:
            self.importer.session.execute(morpheme_count_updater, morpheme_count_tuples)

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
        num_same_expressions = self.importer.session.execute(s).first()[0]

        # Increment counts if expression not in list
        if num_same_expressions == 0:
            s = select([morphemes], 
                from_obj=[expression_consists_of.join(morphemes)], 
                whereclause=expression_consists_of.c.expression_id==expression_id)
            for m in self.importer.session.execute(s):
                if m.id in self.morpheme_count:
                    self.morpheme_count[m.id] += 1
                else:
                    self.morpheme_count[m.id] = (m.expr_count or 0) + 1
        




