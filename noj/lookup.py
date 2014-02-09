#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cProfile as profiler
import gc, pstats, time
import logging
import re
from sqlalchemy.orm import *
from noj.models import Session
from noj import models

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
                  join(models.entry_has_kanji).\
                  join(models.Morpheme).\
                  filter(models.Morpheme.morpheme==search_word)

    # Get the usage examples corresponding to the entry
    return entry_ues_query(session, q_entry_ids)

def kana_query(session, search_word):
    # Note: Having subqueries was profiled to be much faster than relying
    #       on joins. Also need an index on Definition.entry_id

    # Get the entries matching the kana
    q_entry_ids = session.query(models.Entry.id).\
                  join(models.entry_has_kana).\
                  join(models.Morpheme).\
                  filter(models.Morpheme.morpheme==search_word)

    # Get the usage examples corresponding to the entry
    return entry_ues_query(session, q_entry_ids)

def entry_ues_query(session, entry_ids):
    return session.query(models.UsageExample, models.Entry, models.Definition).\
           join(models.definition_has_ues).\
           join(models.Definition).\
           join(models.Entry).\
           filter(models.Entry.id.in_(entry_ids)).\
           options(joinedload_all(models.UsageExample.expression, 
             models.Expression.morpheme_assocs, models.ExpressionConsistsOf.morpheme)).\
           options(joinedload(models.Entry.kana)).\
           options(joinedload(models.Entry.kanji)).\
           options(joinedload(models.Entry.library))

def search_expressions(session, search_word):
    q_text = session.query(models.UsageExample).\
            join(models.Expression).\
            join(models.ExpressionConsistsOf).\
            join(models.Morpheme).\
            filter(models.Morpheme.morpheme==search_word).\
            options(joinedload_all(models.UsageExample.expression, 
                models.Expression.morpheme_assocs, models.ExpressionConsistsOf.morpheme)).\
            options(joinedload_all(models.UsageExample.definitions,
                models.Definition.entry, models.Entry.kana)).\
            options(joinedload_all(models.UsageExample.definitions,
                models.Definition.entry, models.Entry.kanji)).\
            options(joinedload_all(models.UsageExample.definitions,
                models.Definition.entry, models.Entry.library))
    return q_text.all()

def breadcrumb_string(library, entry, definition_list):
    parts = list()
    parts.append(library.breadcrumb_string() or '')
    parts.append(entry.breadcrumb_string() or '')
    # parts.append(definition_list.number, definition_list.definition_list)
    for d in definition_list:
        parts.append(d.breadcrumb_string() or '')
    return u' → '.join(parts)

def main():
    from sqlalchemy import create_engine
    from noj import init_db
    from noj.profiles import ProfileManager

    pm = ProfileManager()
    # pm.database_file = 'jmdict.sqlite'
    pm.database_file = 'daijirin2.sqlite'
    print pm.database_connect_string()

    # search_word = u'面白い'
    search_word = u'先生'
    # search_word = u'悪どい'
    # search_word = u'スポーツ'

    engine = create_engine(pm.database_connect_string(), echo=True)
    init_db(engine)

    session = Session()
    # ues = search_entries(session, search_word)
    ues = search_expressions(session, search_word)
    logging.warning('start')
    # for ue, entry, definition in ues:
    #     print ue.get_n_score()
    #     print ue.expression.expression
    #     print ue.meaning
    #     print breadcrumb_string(entry.library, entry, definition.ancestry())
    #     print
    #     # break
    for ue in ues:
        print ue.get_n_score()
        print ue.expression.expression
        print ue.meaning
        for d in ue.definitions:
            print d.breadcrumb_string(), d.entry.breadcrumb_string()
        print
        break
    logging.warning('done')

    # session.commit()
    session.close()

if __name__ == '__main__':
    main()
