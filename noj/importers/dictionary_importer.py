#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
import os
import re
import json
from pyparsing import *
from lxml import etree
from textwrap import dedent
from noj.misc.uni_printer import UniPrinter
from noj import (
    models,
    db,
    db_constants,
)
from noj.tools.japanese_parser import JapaneseParser
import noj.tools.entry_unformatter as uf

from noj.models import Session

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

    def import_generator(self, session):
        entry_tag = NAMESPACE_PREFIX + 'entry'
        dictionary_meta_tag = NAMESPACE_PREFIX + 'dictionary_meta'

        with open(self.importable_path, 'rb') as f:
            context = etree.iterparse(f, tag=(entry_tag, dictionary_meta_tag))

            lib_id = None
            lib_obj = models.Library(type_id=db_constants.LIB_TYPES_TO_ID['DICTIONARY'],
                                     import_version=__version__)
            morpheme_cache = dict()
            parser = JapaneseParser()

            for action, elem in context:
                if elem.tag == entry_tag:
                    entry_xml = elem
                    self._import_entry(session, entry_xml, lib_id, morpheme_cache, parser)
                    yield f.tell()

                elif elem.tag == dictionary_meta_tag:
                    # Name
                    name_xml = elem.find(NAMESPACE_PREFIX + 'name')
                    lib_obj.name = name_xml.text

                    # Dump version
                    dump_version_xml = elem.find(NAMESPACE_PREFIX + 'dump_version')
                    if dump_version_xml is not None:
                        lib_obj.dump_version = dump_version_xml.text

                    # Convert version
                    convert_version_xml = elem.find(NAMESPACE_PREFIX + 'convert_version')
                    if convert_version_xml is not None:
                        lib_obj.convert_version = convert_version_xml.text

                    # Date
                    date_xml = elem.find(NAMESPACE_PREFIX + 'date')
                    if date_xml is not None:
                        lib_obj.date = date_xml.text

                    # extra
                    extra_text = self._get_extra_text(elem)
                    if extra_text is not None:
                        lib_obj.extra = extra_text

                    lib_id = db.insert_orm(session, lib_obj)[0]

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

    def _import_entry(self, session, entry_xml, lib_id, morpheme_cache, parser):
        entry_obj = models.Entry(library_id=lib_id)

        # Import entry format
        eformat = entry_xml.get('format') or 'J-E1'
        eformat_id = db.insert(session, models.EntryFormat, name=eformat)[0]
        entry_obj.format_id = eformat_id

        # Import kana raw
        if eformat == 'J-J1':
            kana_list = entry_xml.findall(NAMESPACE_PREFIX + 'kana')
            kana_raw_list = list()
            for kana_xml in kana_list:
                kana_raw_list.append(kana_xml.text)
            if kana_raw_list:
                entry_obj.kana_raw = json.dumps(kana_raw_list)

        # Import kanji raw
        if eformat == 'J-J1':
            kanji_list = entry_xml.findall(NAMESPACE_PREFIX + 'kanji')
            kanji_raw_list = list()
            for kanji_xml in kanji_list:
                kanji_raw_list.append(kanji_xml.text)
            if kanji_raw_list:
                entry_obj.kanji_raw = json.dumps(kanji_raw_list)

        # Import accent
        accent_xml = entry_xml.find(NAMESPACE_PREFIX + 'accent')
        if accent_xml is not None:
            entry_obj.accent = accent_xml.text

        # Import extra
        extra_text = self._get_extra_text(entry_xml)
        if extra_text is not None:
            entry_obj.extra = extra_text

        # Import and get id
        entry_id = db.insert_orm(session, entry_obj)[0]

        # Import kana
        kana_list = entry_xml.findall(NAMESPACE_PREFIX + 'kana')
        entry_kana = list()
        if eformat == 'J-J1':
            for i, kana_xml in enumerate(kana_list):
                kana_id = db.insert(session, models.Morpheme, 
                    morpheme=uf.unformat_jj1_kana(kana_xml.text),
                    type_id=db_constants.MORPHEME_TYPES_TO_ID['KANA_ENTRY'],
                    status_id=db_constants.MORPHEME_STATUSES_TO_ID['AUTO'])[0]
                entry_kana.append({'entry_id':entry_id, 'kana_id':kana_id, 'number':i+1})
        else:
            for i, kana_xml in enumerate(kana_list):
                kana_id = db.insert(session, models.Morpheme, morpheme=kana_xml.text,
                    type_id=db_constants.MORPHEME_TYPES_TO_ID['KANA_ENTRY'],
                    status_id=db_constants.MORPHEME_STATUSES_TO_ID['AUTO'])[0]
                entry_kana.append({'entry_id':entry_id, 'kana_id':kana_id, 'number':i+1})
        db.insert_many_core(session, models.entry_has_kana, entry_kana)

        # Import kanji
        kanji_list = entry_xml.findall(NAMESPACE_PREFIX + 'kanji')
        entry_kanji = list()
        if eformat == 'J-J1':
            for i, kanji_xml in enumerate(kanji_list):
                kanji_id = db.insert(session, models.Morpheme, 
                    morpheme=uf.unformat_jj1_kanji(kanji_xml.text, kana_xml.text),
                    type_id=db_constants.MORPHEME_TYPES_TO_ID['KANJI_ENTRY'],
                    status_id=db_constants.MORPHEME_STATUSES_TO_ID['AUTO'])[0]
                entry_kanji.append({'entry_id':entry_id, 'kanji_id':kanji_id, 'number':i+1})
        else:
            for i, kanji_xml in enumerate(kanji_list):
                kanji_id = db.insert(session, models.Morpheme, morpheme=kanji_xml.text,
                    type_id=db_constants.MORPHEME_TYPES_TO_ID['KANJI_ENTRY'],
                    status_id=db_constants.MORPHEME_STATUSES_TO_ID['AUTO'])[0]
                entry_kanji.append({'entry_id':entry_id, 'kanji_id':kanji_id, 'number':i+1})
        db.insert_many_core(session, models.entry_has_kanji, entry_kanji)

        # Import definitions
        root_def_xml = entry_xml.find(NAMESPACE_PREFIX + 'definition')
        self._import_definition(session, root_def_xml, 1, lib_id, entry_id, None, morpheme_cache, parser, eformat)

        return entry_id

    def _import_definition(self, session, definition_xml, number, lib_id, entry_id, 
            parent_id, morpheme_cache, parser, eformat):
        def_obj = models.Definition(entry_id=entry_id, number=number)

        # Import parent
        if parent_id is not None:
            def_obj.parent_id = parent_id

        group = definition_xml.get('group')
        if group is not None:
            def_obj.group = group

        # Import definition text
        def_text_xml = definition_xml.find(NAMESPACE_PREFIX + 'definition_text')
        if def_text_xml is not None:
            def_obj.definition = def_text_xml.text

        # Import extra
        extra_text = self._get_extra_text(definition_xml)
        if extra_text is not None:
            def_obj.extra = extra_text

        # Import and get id
        def_id = db.insert_orm(session, def_obj)[0]

        # Import definition to morpheme map
        if eformat == 'J-J1':
            if def_text_xml is not None:
                morpheme_list = self._import_parse_morphemes(session, def_text_xml.text, 
                                                       morpheme_cache, parser)
                if len(morpheme_list) > 0:
                    for m in morpheme_list:
                        m['definition_id'] = def_id
                    db.insert_many(session, models.DefinitionConsistsOf, 
                                   morpheme_list)

        # Import usage examples
        definition_ues = list()
        ue_list = definition_xml.findall(NAMESPACE_PREFIX + 'usage_example')
        for i, ue_xml in enumerate(ue_list):
            ue_id = self._import_usage_example(session, ue_xml, lib_id, morpheme_cache, parser)
            definition_ues.append({'usage_example_id': ue_id, 'definition_id': def_id,
                                   'number': i+1})

        # Import definition to usage example association
        db.insert_many_core(session, models.definition_has_ues, definition_ues)


        # Import subdefinitions
        subdefinition_list = definition_xml.findall(NAMESPACE_PREFIX + 'definition')
        for i, subdef_xml in enumerate(subdefinition_list):
            self._import_definition(session, subdef_xml, i+1, lib_id, entry_id, def_id, morpheme_cache, parser, eformat)

        return def_id

    def _import_usage_example(self, session, usage_example_xml, lib_id, morpheme_cache, parser):
        ue_obj = models.UsageExample(library_id=lib_id)

        # Import usage example type
        ue_type = usage_example_xml.get('type') or 'UNKNOWN'
        ue_type = ue_type.upper()
        ue_type_id = db.insert(session, models.UEType, name=ue_type)[0]
        ue_obj.type_id = ue_type_id

        # Import expression
        expression_xml = usage_example_xml.find(NAMESPACE_PREFIX + 'expression')
        expression_id = self._import_expression(session, expression_xml, morpheme_cache, parser)
        ue_obj.expression_id = expression_id

        # Import reading
        reading_xml = usage_example_xml.find(NAMESPACE_PREFIX + 'reading')
        if reading_xml is not None:
            ue_obj.reading = reading_xml.text

        # Import meaning
        meaning_xml = usage_example_xml.find(NAMESPACE_PREFIX + 'meaning')
        if meaning_xml is not None:
            ue_obj.meaning = meaning_xml.text

        # Import sound
        sound_xml = usage_example_xml.find(NAMESPACE_PREFIX + 'sound')
        if sound_xml is not None:
            ue_obj.sound = sound_xml.text

        # Import image
        image_xml = usage_example_xml.find(NAMESPACE_PREFIX + 'image')
        if image_xml is not None:
            ue_obj.image = image_xml.text

        # Import extra
        extra_text = self._get_extra_text(usage_example_xml)
        if extra_text is not None:
            ue_obj.extra = extra_text

        # Import validated
        is_validated = usage_example_xml.get('validated')
        if is_validated == 'false':
            is_validated = 0
        elif is_validated == 'true':
            is_validated = 1
        else:
            is_validated = 1
        ue_obj.is_validated = is_validated

        # Import and get id
        ue_id = db.insert_orm(session, ue_obj)[0]

        return ue_id

    def _import_parse_morphemes(self, session, line, morpheme_cache, parser):
        results = parser.parse(line or '')

        # For bulk inserting the morpheme-expression association tuples
        morpheme_list = list()  # list of dicts representing fields

        for m in results:
            # Insert or get morpheme, (morpheme, type_id) unique
            morpheme_key = (m.base, m.type_)
            if morpheme_key in morpheme_cache:
                morpheme_id = morpheme_cache[morpheme_key]
            else:
                morpheme_id, new_morpheme, morpheme = db.insert_get(session, 
                    models.Morpheme, morpheme=m.base, type_id=m.type_,
                    status_id=db_constants.MORPHEME_STATUSES_TO_ID['AUTO'])
                morpheme_cache[morpheme_key] = morpheme_id

            # Bulk insert later
            morpheme_list.append({'morpheme_id':morpheme_id,
                                  'position':m.position, 
                                  'word_length':m.length,
                                  'conjugation':m.morpheme,
                                  'reading':m.reading})

        return morpheme_list

    def _import_expression(self, session, expression_xml, morpheme_cache, parser):
        expression_id, new = db.insert(session, models.Expression, 
                                       expression=expression_xml.text)
        if new:
            morpheme_list = self._import_parse_morphemes(session, expression_xml.text, 
                                                   morpheme_cache, parser)
            if len(morpheme_list) > 0:
                for m in morpheme_list:
                    m['expression_id'] = expression_id
                db.insert_many(session, models.ExpressionConsistsOf, 
                               morpheme_list)

        return expression_id

def main():
    from sqlalchemy import create_engine
    from noj import init_db
    engine = create_engine('sqlite:///../../test.sqlite', echo=False)
    init_db(engine)
    schema_path = '../../schema5.xsd'
    importable_path = '../converters/daijirin2/daijirin2_importable.xml'
    # importable_path = '../converters/jmdict/jmdict-importable.xml'
    # importable_path = '../../example5.xml'

    import progressbar as pb
    widgets = ['Importing: ', pb.Percentage(), ' ', pb.Bar(),
               ' ', pb.Timer(), ' ']

    session = Session()
    importer = DictionaryImporter(importable_path)
    importer.validate_schema(schema_path)

    pbar = pb.ProgressBar(widgets=widgets, maxval=len(importer)).start()
    for i in importer.import_generator(session):
        pbar.update(i)

    session.commit()
    session.close()
    pbar.finish()

if __name__ == '__main__':
    main()

