#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cProfile as profiler
import gc, pstats, time
import logging
import re
import json
from sqlalchemy.orm import *
from noj.model import models
from noj.model.models import Session
import noj.tools.entry_unformatter as uf

kanji = map(unichr, range(0x4e00, 0x9fbf + 1))
katakana = map(unichr, range(0x30a0, 0x30ff + 1))
hiragana = map(unichr, range(0x3040, 0x309f + 1))
japanese = ''.join(kanji + katakana + hiragana)
kana = ''.join(katakana + hiragana)
kana_matcher = re.compile(r'^[%s\s]+$' % kana, re.U)

logging.basicConfig(format='%(asctime)s %(message)s')

def profile(fn):
    def wrapper(*args, **kw):
        elapsed, stat_loader, result = _profile("foo.txt", fn, *args, **kw)
        stats = stat_loader()
        stats.sort_stats('cumulative')
        stats.print_stats()
        # uncomment this to see who's calling what
        # stats.print_callers()
        return result
    return wrapper

def _profile(filename, fn, *args, **kw):
    load_stats = lambda: pstats.Stats(filename)
    gc.collect()

    began = time.time()
    profiler.runctx('result = fn(*args, **kw)', globals(), locals(),
                    filename=filename)
    ended = time.time()

    return ended - began, load_stats, locals()['result']

def search_entries(session, search_word):
    m = kana_matcher.match(search_word)
    if m:
        logging.warning('kana search')
        ues = kana_query(session, search_word).all()
        logging.warning('search complete')
        return ues
    else:
        logging.warning('kanji search')
        ues = kanji_query(session, search_word).all()
        logging.warning('search complete')
        return ues

# @profile
def kanji_query(session, search_word):
    # Note: Having subqueries was profiled to be much faster than relying
    #       on joins. Also need an index on Definition.entry_id

    # Get the entries matching the kanji
    q_entry_ids = session.query(models.Entry.id).\
                  join(models.EntryHasKanji).\
                  join(models.Morpheme).\
                  filter(models.Morpheme.morpheme==search_word)

    # Get the usage examples corresponding to the entry
    return entry_ues_query(session, q_entry_ids)

def kana_query(session, search_word):
    # Note: Having subqueries was profiled to be much faster than relying
    #       on joins. Also need an index on Definition.entry_id

    # Get the entries matching the kana
    q_entry_ids = session.query(models.Entry.id).\
                  join(models.EntryHasKana).\
                  join(models.Morpheme).\
                  filter(models.Morpheme.morpheme==search_word)

    # Get the usage examples corresponding to the entry
    return entry_ues_query(session, q_entry_ids)

def entry_ues_query(session, entry_ids):
    return session.query(models.UsageExample, models.Entry, models.Definition).\
           join(models.DefinitionHasUEs).\
           join(models.Definition).\
           join(models.Entry).\
           filter(models.Entry.id.in_(entry_ids)).\
           options(joinedload_all(models.UsageExample.expression, 
             models.Expression.morpheme_assocs, models.ExpressionConsistsOf.morpheme)).\
           options(joinedload_all(models.Entry.kana_assocs, models.EntryHasKana.kana)).\
           options(joinedload_all(models.Entry.kanji_assocs, models.EntryHasKanji.kanji)).\
           options(joinedload(models.Entry.library))

def search_expressions(session, search_word):
    q_text = session.query(models.UsageExample).\
            join(models.Expression).\
            join(models.ExpressionConsistsOf).\
            join(models.Morpheme).\
            filter(models.Morpheme.morpheme==search_word).\
            options(joinedload_all(models.UsageExample.expression, 
                models.Expression.morpheme_assocs, models.ExpressionConsistsOf.morpheme)).\
            options(joinedload_all(models.UsageExample.definition_assocs,
                models.DefinitionHasUEs.definition, models.Definition.entry, 
                models.Entry.kana_assocs, models.EntryHasKana.kana)).\
            options(joinedload_all(models.UsageExample.definition_assocs,
                models.DefinitionHasUEs.definition, models.Definition.entry, 
                models.Entry.kanji_assocs, models.EntryHasKanji.kanji)).\
            options(joinedload_all(models.UsageExample.definition_assocs,
                models.DefinitionHasUEs.definition, models.Definition.entry, 
                models.Entry.library))
    return q_text.all()

class LookupResult(object):
    """docstring for LookupResult"""
    def __init__(self, search_word, usage_example, definition=None, entry=None):
        super(LookupResult, self).__init__()
        self.search_word = search_word
        self.usage_example = usage_example
        self.definition = definition
        self.entry = entry
        self.preload()

    def __unicode__(self):
        return u'{e_score}\n{expr}\n{meaning}\n{source}'.format(
            e_score=self.get_expression_score(),
            expr=self.get_expression_for_view(),
            meaning=self.get_meaning_for_view(),
            source=self.get_source_for_view())

    def preload(self):
        pass

    def get_expression_for_view(self, replace_blanks=True):
        if replace_blanks == False:
            return self.get_expression()
        return self.get_expression_replace_blanks()

    def get_meaning_for_view(self, def_as_meaning=True):
        if self.usage_example.meaning is None and def_as_meaning:
            return self.get_definition_as_meaning()
        return self.get_meaning()

    def get_source_for_view(self):
        if self.definition is None or self.entry is None:
            return self._get_source_unspecified()
        else:
            return self._get_source_specified()

    def _get_source_unspecified(self):
        entries     = set()
        definitions = set()

        definition_assocs = self.usage_example.definition_assocs
        for da in definition_assocs:
            definitions.add(da.definition)

        for d in definitions:
            entries.add(d.entry)

        # TODO: remove the <EXS> etc. tags?
        parts = list()
        parts.append(self.usage_example.library.breadcrumb_string() or '')
        if len(entries) == 1:
            entry = entries.pop()
            parts.append(entry.breadcrumb_string() or '')
            if len(definitions) == 1:
                definition = definitions.pop()
                for d in definition.ancestry():
                    parts.append(d.breadcrumb_string() or '')
            elif len(definitions) > 1:
                parts.append("(Multiple definitions)")
        elif len(entries) > 1:
            parts.append("(Multiple entries)")
            
        return u' → '.join(parts)

    def _get_source_specified(self):
        # TODO: remove the <EXS> etc. tags?
        parts = list()
        parts.append(self.entry.library.breadcrumb_string() or '')
        parts.append(self.entry.breadcrumb_string() or '')
        for d in self.definition.ancestry():
            parts.append(d.breadcrumb_string() or '')

        return u' → '.join(parts)

    def get_usage_example_id(self):
        return self.usage_example.id

    def get_definition_ids(self):
        if self.definition is None:
            definitions = set()

            definition_assocs = self.usage_example.definition_assocs
            for da in definition_assocs:
                definitions.add(da.definition)

            return [d.id for d in definitions]
        return (self.definition.id,)

    def get_entry_ids(self):
        if self.entry is None:
            entries     = set()
            definitions = set()

            definition_assocs = self.usage_example.definition_assocs
            for da in definition_assocs:
                definitions.add(da.definition)

            for d in definitions:
                entries.add(d.entry)

            return [e.id for e in entries]
        return (self.entry.id,)

    def get_expression(self):
        return self.usage_example.expression.expression

    def get_expression_replace_blanks(self):
        entry = self.entry
        if entry is None:
            entries     = set()
            definitions = set()

            definition_assocs = self.usage_example.definition_assocs
            for da in definition_assocs:
                definitions.add(da.definition)

            for d in definitions:
                entries.add(d.entry)

            if len(entries) != 1:
                return self.get_expression()

            entry = entries.pop()

        raw_kana_json = entry.kana_raw
        raw_kanji_json = entry.kanji_raw
        if raw_kana_json is None:
            return self.get_expression()

        full = None
        stem = None
        try:
            raw_kana_list = json.loads(raw_kana_json)
            kana_replacer = raw_kana_list[0]
            if raw_kanji_json is not None:
                raw_kanji_list = json.loads(raw_kanji_json)
                kanji_replacer = raw_kanji_list[0]
                full = uf.jj1_kanji_full(kanji_replacer, kana_replacer)
                stem = uf.jj1_kanji_stem(kanji_replacer, kana_replacer)
            else:
                full = uf.jj1_kana_full(kana_replacer)
                stem = uf.jj1_kana_stem(kana_replacer)
        except Exception as e:
            print 'failed to replace blanks in expression', e
            return self.get_expression()

        expression = self.usage_example.expression.expression
        if stem is not None:
            expression = expression.replace(u'―・', stem)
            expression = expression.replace(u'―∘', stem)
        if full is not None:
            expression = expression.replace(u'―', full)
        
        return expression

    def get_meaning(self):
        return self.usage_example.meaning

    def get_definition_as_meaning(self):
        # TODO: remove the <EXS> etc. tags?
        # parts = list()
        # for d in self.definition.ancestry():
        #     if d.definition is not None and d.definition != '':
        #         parts.append(d.definition)
        # definition_line = u' → '.join(parts)
        definition_line = self.definition.definition or ''
        definition_line = definition_line.replace(u'\n', u' ')
        entry_line = self.entry.breadcrumb_string()

        # return u' → '.join(parts)
        return u'{}: {}'.format(entry_line, definition_line)

    def get_reading(self):
        pass

    def get_source_line(self):
        return breadcrumb_string(self.entry.library, self.entry, self.definition.ancestry())

    def get_source_line_components(self):
        pass

    def get_expression_score(self):
        return self.usage_example.get_n_score()

    def get_definition_score(self):
        return self.usage_example.get_n_score()

    def get_image(self):
        return self.usage_example.image

    def get_sound(self):
        return self.usage_example.sound

    def get_format(self):
        return self.entry.format_id

    def is_known(self):
        pass

    def is_j_to_j(self):
        pass

    def is_validated(self):
        # TODO: THIS IS WRONG
        return self.usage_example.is_validated
        

def main():
    import sys
    from sqlalchemy import create_engine
    from noj import init_db
    from noj.model.profiles import ProfileManager

    pm = ProfileManager()
    pm.database_file = 'jmdict.sqlite'
    # pm.database_file = 'daijirin2.sqlite'
    print pm.database_connect_string()

    search_word = u'面白い'
    # search_word = u'先生'
    # search_word = u'悪どい'
    # search_word = u'スポーツ'
    search_word = u'生く'
    if len(sys.argv) == 2:
        print sys.getdefaultencoding()
        search_word = sys.argv[1].decode(sys.stdin.encoding)

    engine = create_engine(pm.database_connect_string(), echo=True)
    init_db(engine)

    session = Session()
    ues = search_entries(session, search_word)
    # ues = search_expressions(session, search_word)
    logging.warning('start')
    # for ue, entry, definition in ues:
    #     print ue.get_n_score()
    #     print ue.expression.expression
    #     print ue.meaning
    #     print breadcrumb_string(entry.library, entry, definition.ancestry())
    #     print
    #     break
    for ue, entry, definition in ues:
        res = LookupResult(search_word, ue, definition, entry)
        print unicode(res).encode(sys.stdout.encoding, errors='replace')
        # print res.get_expression_replace_blanks().encode(sys.stdout.encoding, errors='replace')
        break
    # for ue in ues:
    #     res = LookupResult(search_word, ue)
    #     print unicode(res)
    #     print res.get_expression_replace_blanks().encode(sys.stdout.encoding, errors='replace')
    #     break
    # for ue in ues:
    #     print ue.get_n_score()
    #     print ue.expression.expression
    #     print ue.meaning
    #     for d in ue.definition_assocs:
    #         print d.number, d.definition.breadcrumb_string(), d.definition.entry.breadcrumb_string()
    #     print
    #     break
    logging.warning('done')

    # session.commit()
    session.close()

if __name__ == '__main__':
    main()
