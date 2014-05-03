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
from noj.importers.abstract_importer import AbstractImporterVisitor

from noj.model.models import Session

__version__ = '1.0.0a'

pp = UniPrinter(indent=4)

NAMESPACE_URI = "http://www.naturalorderjapanese.com"
NAMESPACE_PREFIX = "{" + NAMESPACE_URI + "}"

class DictionaryWalker(object):
    """Import XML dictionary files into the database."""
    def __init__(self, importable_path):
        super(DictionaryWalker, self).__init__()
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
                    self._entry_accept(entry_xml, visitor)
                    yield f.tell()

                elif elem.tag == dictionary_meta_tag:
                    visitor.visit_library()

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
        visitor.visit_finish()

    def _get_extra_text(self, elem):
        extra_list = elem.findall(NAMESPACE_PREFIX + 'extra')
        extra_dict = dict()
        for extra_xml in extra_list:
            extra_name = extra_xml.get('name')
            extra_dict[extra_name] = extra_xml.text
        if extra_dict:
            return json.dumps(extra_dict)
        return None

    def _entry_accept(self, entry_xml, visitor):
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
        self._definition_accept(root_def_xml, 1, visitor)

    def _definition_accept(self, definition_xml, number, visitor):
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

        # Import usage examples
        ue_list = definition_xml.findall(NAMESPACE_PREFIX + 'usage_example')
        for i, ue_xml in enumerate(ue_list):
            self._usage_example_accept(ue_xml, i+1, visitor)

        # Import definition to usage example association
        visitor.visit_finish_definition_ues()

        # Import subdefinitions
        subdefinition_list = definition_xml.findall(NAMESPACE_PREFIX + 'definition')
        for i, subdef_xml in enumerate(subdefinition_list):
            self._definition_accept(subdef_xml, i+1, visitor)

        visitor.visit_finish_definition()

    def _usage_example_accept(self, usage_example_xml, number, visitor):
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


class DictionaryImporterVisitor(AbstractImporterVisitor):
    """docstring for DictionaryImporterVisitor"""
    def __init__(self, session, parser):
        super(DictionaryImporterVisitor, self).__init__(session, parser)

    def get_import_version(self):
        return __version__

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
    importer = DictionaryWalker(importable_path)
    parser = JapaneseParser()
    visitor = DictionaryImporterVisitor(session, parser)
    importer.validate_schema(schema_path)

    pbar = pb.ProgressBar(widgets=widgets, maxval=len(importer)).start()
    for i in importer.import_generator(visitor):
        pbar.update(i)

    session.commit()
    session.close()
    pbar.finish()

if __name__ == '__main__':
    main()

