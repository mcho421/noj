#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
import os
import sys
import re
import json
from pyparsing import *
from lxml import etree
from textwrap import dedent
from noj.misc.uni_printer import UniPrinter
from noj.model import (
    models,
    db,
    db_constants,
)
from noj.tools.japanese_parser import JapaneseParser
import noj.tools.entry_unformatter as uf

from noj.model.models import Session

__version__ = '1.0.0a'

pp = UniPrinter(indent=4)

NAMESPACE_URI = "http://www.naturalorderjapanese.com"
NAMESPACE_PREFIX = "{" + NAMESPACE_URI + "}"

class DictionaryImporter(object):
    """Import XML dictionary files into the database."""
    def __init__(self, importable_path):
        super(DictionaryImporter, self).__init__()
        self.importable_path = importable_path

    def __len__(self):
        return os.path.getsize(self.importable_path)

    def validate_schema(self, schema_path):
        xmlschema_doc = etree.parse(schema_path)
        xmlschema = etree.XMLSchema(xmlschema_doc)

        print 'parsing'
        doc = etree.parse(self.importable_path) 
        print 'validating'
        # print xmlschema.validate(doc)
        xmlschema.assertValid(doc)

    def import_generator(self, visitor):
        entry_tag = NAMESPACE_PREFIX + 'entry'
        dictionary_meta_tag = NAMESPACE_PREFIX + 'dictionary_meta'

        with open(self.importable_path, 'rb') as f:
            context = etree.iterparse(f, tag=(entry_tag, dictionary_meta_tag))

            for action, elem in context:
                if elem.tag == entry_tag:
                    entry_xml = elem
                    self._import_entry(entry_xml, visitor)
                    yield f.tell()

                elif elem.tag == dictionary_meta_tag:
                    # Name
                    name_xml = elem.find(NAMESPACE_PREFIX + 'name')
                    visitor.visit_library_name(name_xml.text)

                    # Dump version
                    dump_version_xml = elem.find(NAMESPACE_PREFIX + 'dump_version')
                    if dump_version_xml is not None:
                        visitor.visit_library_dump_version(dump_version_xml.text)

                    # Convert version
                    convert_version_xml = elem.find(NAMESPACE_PREFIX + 'convert_version')
                    if convert_version_xml is not None:
                        visitor.visit_library_convert_version(convert_version_xml.text)

                    # Date
                    date_xml = elem.find(NAMESPACE_PREFIX + 'date')
                    if date_xml is not None:
                        visitor.visit_library_date(date_xml.text)

                    # extra
                    extra_text = self._get_extra_text(elem)
                    if extra_text is not None:
                        visitor.visit_library_extra(extra_text)

                    visitor.visit_finish_library()

                elem.clear()

    def _get_extra_text(self, elem):
        extra_list = elem.findall(NAMESPACE_PREFIX + 'extra')
        extra_dict = dict()
        for extra_xml in extra_list:
            extra_name = extra_xml.get('name')
            extra_dict[extra_name] = extra_xml.text
        if extra_dict:
            return json.dumps(extra_dict)
        return None

    def _import_entry(self, entry_xml, visitor):
        visitor.visit_entry()

        # Import entry format
        self.eformat = entry_xml.get('format') or 'J-E1'
        visitor.visit_entry_format(self.eformat)

        # Import kana raw
        if self.eformat == 'J-J1':
            kana_list = entry_xml.findall(NAMESPACE_PREFIX + 'kana')
            kana_raw_list = list()
            for kana_xml in kana_list:
                kana_raw_list.append(kana_xml.text)
            if kana_raw_list:
                visitor.visit_kana_raw_list(kana_raw_list)

        # Import kanji raw
        if self.eformat == 'J-J1':
            kanji_list = entry_xml.findall(NAMESPACE_PREFIX + 'kanji')
            kanji_raw_list = list()
            for kanji_xml in kanji_list:
                kanji_raw_list.append(kanji_xml.text)
            if kanji_raw_list:
                visitor.visit_kanji_raw_list(kanji_raw_list)

        # Import accent
        accent_xml = entry_xml.find(NAMESPACE_PREFIX + 'accent')
        if accent_xml is not None:
            visitor.visit_accent(accent_xml.text)

        # Import extra
        extra_text = self._get_extra_text(entry_xml)
        if extra_text is not None:
            visitor.visit_entry_extra(extra_text)

        # Import and get id
        visitor.visit_construct_entry()

        # Import kana
        kana_list_xml = entry_xml.findall(NAMESPACE_PREFIX + 'kana')
        kana_list = [kana_xml.text for kana_xml in kana_list_xml]
        if kana_list:
            visitor.visit_kana_list(kana_list)

        # Import kanji
        kanji_list_xml = entry_xml.findall(NAMESPACE_PREFIX + 'kanji')
        kanji_list = [kanji_xml.text for kanji_xml in kanji_list_xml]
        if kanji_list:
            visitor.visit_kanji_list(kanji_list)

        # Import definitions
        root_def_xml = entry_xml.find(NAMESPACE_PREFIX + 'definition')
        self._import_definition(root_def_xml, 1, visitor)

    def _import_definition(self, definition_xml, number, visitor):
        visitor.visit_definition(number)

        group = definition_xml.get('group')
        if group is not None:
            visitor.visit_definition_group(group)

        # Import definition text
        def_text_xml = definition_xml.find(NAMESPACE_PREFIX + 'definition_text')
        def_text = None
        if def_text_xml is not None:
            def_text = def_text_xml.text
            visitor.visit_definition_text(def_text)

        # Import extra
        extra_text = self._get_extra_text(definition_xml)
        if extra_text is not None:
            visitor.visit_definition_extra(extra_text)

        # Import and get id
        visitor.visit_construct_definition()

        # Import definition to morpheme map
        visitor.visit_definition_morpheme_map(def_text)

        # Import usage examples
        ue_list = definition_xml.findall(NAMESPACE_PREFIX + 'usage_example')
        for i, ue_xml in enumerate(ue_list):
            self._import_usage_example(ue_xml, i+1, visitor)

        # Import definition to usage example association
        visitor.visit_before_definition_recurse()

        # Import subdefinitions
        subdefinition_list = definition_xml.findall(NAMESPACE_PREFIX + 'definition')
        for i, subdef_xml in enumerate(subdefinition_list):
            self._import_definition(subdef_xml, i+1, visitor)

        visitor.visit_finish_definition()

    def _import_usage_example(self, usage_example_xml, number, visitor):
        ue_type = usage_example_xml.get('type') or 'UNKNOWN'
        visitor.visit_usage_example(ue_type)

        # Import expression
        expression_xml = usage_example_xml.find(NAMESPACE_PREFIX + 'expression')
        visitor.visit_expression(expression_xml.text)

        # Import reading
        reading_xml = usage_example_xml.find(NAMESPACE_PREFIX + 'reading')
        if reading_xml is not None:
            visitor.visit_ue_reading(reading_xml.text)

        # Import meaning
        meaning_xml = usage_example_xml.find(NAMESPACE_PREFIX + 'meaning')
        if meaning_xml is not None:
            visitor.visit_meaning(meaning_xml.text)

        # Import sound
        sound_xml = usage_example_xml.find(NAMESPACE_PREFIX + 'sound')
        if sound_xml is not None:
            visitor.visit_sound(sound_xml.text)

        # Import image
        image_xml = usage_example_xml.find(NAMESPACE_PREFIX + 'image')
        if image_xml is not None:
            visitor.visit_image(image_xml.text)

        # Import extra
        extra_text = self._get_extra_text(usage_example_xml)
        if extra_text is not None:
            visitor.visit_ue_extra(extra_text)

        # Import validated
        is_validated = usage_example_xml.get('validated')
        if is_validated == 'false':
            is_validated = 0
        elif is_validated == 'true':
            is_validated = 1
        else:
            is_validated = 1
        visitor.visit_ue_validated(is_validated)
        visitor.visit_finish_usage_example(number)


class DictionaryImporterVisitor(object):
    """docstring for DictionaryImporterVisitor"""
    def __init__(self, session):
        super(DictionaryImporterVisitor, self).__init__()
        self.session = session
        self.lib_id = None
        self.lib_obj = models.Library(type_id=db_constants.LIB_TYPES_TO_ID['DICTIONARY'],
                                 import_version=__version__)
        self.morpheme_cache = dict()
        self.parser = JapaneseParser()
        self.entry_obj = None
        self.entry_id = None
        self.eformat = None
        self.last_kana_text = None
        self.def_id_stack = list()
        self.parent_id = None
        self.def_id = None
        self.definition_ues = None

        self.ue_obj = None

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
        self.parent_id = self.def_id
        self.def_id = None
        self.definition_ues = list()

        self.def_obj = models.Definition(entry_id=self.entry_id, number=number)

        # Import parent
        if self.parent_id is not None:
            self.def_obj.parent_id = self.parent_id

    def visit_definition_group(self, group):
        self.def_obj.group = group

    def visit_definition_text(self, text):
        self.def_obj.definition = text

    def visit_definition_extra(self, extra):
        self.def_obj.extra = extra

    def visit_construct_definition(self):
        self.def_id = db.insert_orm(self.session, self.def_obj)[0]

    def visit_definition_morpheme_map(self, def_text):
        if self.eformat == 'J-J1':
            if def_text is not None:
                morpheme_list = self._import_parse_morphemes(def_text)
                if len(morpheme_list) > 0:
                    for m in morpheme_list:
                        m['definition_id'] = self.def_id
                    db.insert_many(self.session, models.DefinitionConsistsOf, 
                                   morpheme_list)

    def visit_finish_definition(self):
        self.def_id = self.def_id_stack.pop()


    def visit_usage_example(self, ue_type):
        self.ue_obj = models.UsageExample(library_id=self.lib_id)

        ue_type = ue_type.upper()
        ue_type_id = db.insert(self.session, models.UEType, name=ue_type)[0]
        self.ue_obj.type_id = ue_type_id

    def visit_before_definition_recurse(self):
        db.insert_many(self.session, models.DefinitionHasUEs, self.definition_ues)

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

    def visit_finish_usage_example(self, number):
        if self.ue_obj is not None:
            ue_id, new = db.insert_orm(self.session, self.ue_obj)

            self.definition_ues.append({'usage_example_id': ue_id, 'definition_id': self.def_id,
                                   'number': number})

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


def main():
    from sqlalchemy import create_engine
    from noj import init_db
    engine = create_engine('sqlite:///../../test.sqlite', echo=False)
    init_db(engine)
    schema_path = '../../schemas/dictionary_schema_1.0.0a.xsd'
    # importable_path = '../converters/daijirin2/daijirin2_importable.xml'
    #importable_path = '../converters/jmdict/jmdict-importable.xml'
    importable_path = sys.argv[1]
    # importable_path = '../../schemas/example_dictionary_1.0.0a.xml'

    import progressbar as pb
    widgets = ['Importing: ', pb.Percentage(), ' ', pb.Bar(),
               ' ', pb.Timer(), ' ']

    session = Session()
    importer = DictionaryImporter(importable_path)
    visitor = DictionaryImporterVisitor(session)
    importer.validate_schema(schema_path)

    pbar = pb.ProgressBar(widgets=widgets, maxval=len(importer)).start()
    for i in importer.import_generator(visitor):
        pbar.update(i)

    session.commit()
    session.close()
    pbar.finish()

if __name__ == '__main__':
    main()

