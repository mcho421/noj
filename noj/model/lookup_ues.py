#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
import json
from sqlalchemy.orm import *
from noj.model import models
from noj.model.models import Session
import noj.tools.entry_unformatter as uf
import lookup_adts as adts

kanji = map(unichr, range(0x4e00, 0x9fbf + 1))
katakana = map(unichr, range(0x30a0, 0x30ff + 1))
hiragana = map(unichr, range(0x3040, 0x309f + 1))
japanese = ''.join(kanji + katakana + hiragana)
kana = ''.join(katakana + hiragana)
kana_matcher = re.compile(r'^[%s\s]+$' % kana, re.U)


class LookupUEs(object):
    def __init__(self):
        super(LookupUEs, self).__init__()

    @classmethod
    def lookup_entries(cls, session, search_word, limit=None, offset=None):
        return cls._lookup_entries_by_kanji(session, search_word, limit, offset)

    @classmethod
    def lookup_ues_by_entry(cls, session, search_word, limit=None, offset=None):
        m = kana_matcher.match(search_word)
        if m:
            logging.info('kana search')
            ues = cls._lookup_ues_by_kana(session, search_word, limit, offset)
            logging.info('search complete')
            return ues
        else:
            logging.info('kanji search')
            ues = cls._lookup_ues_by_kanji(session, search_word, limit, offset)
            logging.info('search complete')
            return ues

    @classmethod
    def lookup_ues_by_definition(cls, session, search_word, limit=None, offset=None):
        # TODO: need to test
        q_text = session.query(models.UsageExample).\
                join(models.Definition).\
                join(models.DefinitionConsistsOf).\
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
        return cls._text_query_to_result_list(q_text, search_word, limit, offset)

    @classmethod
    def lookup_ues_by_expression(cls, session, search_word, limit=None, offset=None):
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
        return cls._text_query_to_result_list(q_text, search_word, limit, offset)

    @classmethod
    def _lookup_ues_by_kana(cls, session, search_word, limit=None, offset=None):
        # Note: Having subqueries was profiled to be much faster than relying
        #       on joins. Also need an index on Definition.entry_id

        # Get the entries matching the kana
        q_entry_ids = session.query(models.Entry.id).\
                      join(models.EntryHasKana).\
                      join(models.Morpheme).\
                      filter(models.Morpheme.morpheme==search_word)

        # Get the usage examples corresponding to the entry
        query = cls._entry_ues_query(session, q_entry_ids)
        return cls._entry_query_to_result_list(query, search_word, limit, offset)

    @classmethod
    def _lookup_ues_by_kanji(cls, session, search_word, limit=None, offset=None):
        # Note: Having subqueries was profiled to be much faster than relying
        #       on joins. Also need an index on Definition.entry_id

        # Get the entries matching the kanji
        q_entry_ids = session.query(models.Entry.id).\
                      join(models.EntryHasKanji).\
                      join(models.Morpheme).\
                      filter(models.Morpheme.morpheme==search_word)

        # Get the usage examples corresponding to the entry
        query = cls._entry_ues_query(session, q_entry_ids)
        return cls._entry_query_to_result_list(query, search_word, limit, offset)

    @classmethod
    def _entry_ues_query(cls, session, entry_ids):
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

    @classmethod
    def _lookup_entries_by_kanji(cls, session, search_word, limit=None, offset=None):
        # Maybe just adapt the ue version
        # q_entry_ids = session.query(models.Entry.id).\
        #               join(models.EntryHasKanji).\
        #               join(models.Morpheme).\
        #               filter(models.Morpheme.morpheme==search_word)
        # query = session.query(models.UsageExample, models.Library, models.Entry, models.Definition).\
        #        join(models.DefinitionHasUEs).\
        #        join(models.Definition).\
        #        join(models.Entry).\
        #        filter(models.Entry.id.in_(q_entry_ids)).\
        #        options(joinedload_all(models.UsageExample.expression, 
        #          models.Expression.morpheme_assocs, models.ExpressionConsistsOf.morpheme)).\
        #        options(joinedload_all(models.Entry.kana_assocs, models.EntryHasKana.kana)).\
        #        options(joinedload_all(models.Entry.kanji_assocs, models.EntryHasKanji.kanji)).\
        #        options(joinedload(models.Entry.library))
        query = session.query(models.Entry).\
                join(models.EntryHasKanji).\
                join(models.Morpheme).\
                filter(models.Morpheme.morpheme==search_word).\
                options(joinedload(models.Entry.library)).\
                options(joinedload(models.Entry.definitions)).\
                options(joinedload_all(models.Entry.kana_assocs, models.EntryHasKana.kana)).\
                options(joinedload_all(models.Entry.kanji_assocs, models.EntryHasKanji.kanji))
        # result = query.all()
        # for ue, lib, entry, definition in result:
            # print ue, lib, entry, definition
        # count = cls._query_count(query)
        res = cls._query_paging(query, limit, offset).all()
        # dict_result = adts.DictionaryResult(count=count)
        # print 'dict:', unicode(dict_result)
        # for ue, lib, entry, definition in res:
        #     print "as"
        #     if lib not in dict_result:
        #         dict_result[lib] = adts.LibraryResult(lib, count=count)
        #     lib_result = dict_result[lib]

        #     if entry not in lib_result:
        #         lib_result[entry] = adts.EntryResult(entry, count=count)
        #     entry_result = lib_result[entry]

        #     if definition not in entry_result:
        #         entry_result[definition] = adts.DefinitionResult(definition, count=count)
        #     def_result = entry_result[definition]

        #     ue_result = adts.UEResult(search_word, ue, definition, entry)
        #     def_result.append(ue_result)
        # return dict_result
        entry_list = adts.EntryList()
        for entry in res:
            entry_list.append(entry)
        return entry_list
        # return res


    @classmethod
    def _query_paging(cls, query, limit, offset):
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    @classmethod
    def _query_count(cls, query):
        count = query.count()
        print count
        return count

    @classmethod
    def _entry_query_to_result_list(cls, query, search_word, limit, offset):
        count = cls._query_count(query)
        res = cls._query_paging(query, limit, offset).all()
        result_list = adts.UEResultList(count)
        for ue, entry, definition in res:
            ue_result = adts.UEResult(search_word, ue, definition, entry)
            result_list.append(ue_result)
        return result_list

    @classmethod
    def _text_query_to_result_list(cls, query, search_word, limit, offset):
        count = cls._query_count(query)
        res = cls._query_paging(query, limit, offset).all()
        result_list = adts.UEResultList(count)
        for ue in res:
            ue_result = adts.UEResult(search_word, ue)
            result_list.append(ue_result)
        return result_list

def main():
    import sys
    from sqlalchemy import create_engine
    from noj import init_db
    from noj.model.profiles import ProfileManager

    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    pm = ProfileManager()
    pm.database_file = 'jmdict.sqlite'
    # pm.database_file = 'daijirin2.sqlite'
    print pm.database_connect_string()

    # search_word = u'面白い'
    # search_word = u'先生'
    # search_word = u'悪どい'
    # search_word = u'スポーツ'
    # search_word = u'生く'
    search_word = u'怪物'

    if len(sys.argv) == 2:
        print sys.getdefaultencoding()
        search_word = sys.argv[1].decode(sys.stdin.encoding)

    engine = create_engine(pm.database_connect_string(), echo=True)
    init_db(engine)

    session = Session()
    lookup = LookupUEs()

    logging.info('start')
    # ues = lookup.lookup_ues_by_entry(session, search_word, 100)
    # ues = lookup.lookup_ues_by_expression(session, search_word, 100)
    dict_result = lookup.lookup_entries(session, search_word, 100)
    print 'dict:', unicode(dict_result)
    logging.info('done')
    # ues = lookup.lookup_ues_by_entry(session, u'先生')
    # print len(ues)
    # return
    # ues = search_expressions(session, search_word)

    # print unicode(ues)
    # print ues.get_count(), len(ues)

    # for ue, entry, definition in ues:
    #     print ue.get_n_score()
    #     print ue.expression.expression
    #     print ue.meaning
    #     print
        # break
    # for ue in ues:
    #     print ue.get_n_score()
    #     print ue.expression.expression
    #     print ue.meaning
    #     for d in ue.definition_assocs:
    #         print d.number, d.definition.breadcrumb_string(), d.definition.entry.breadcrumb_string()
    #     print
    #     break
    logging.info('done')

    # session.commit()
    session.close()

if __name__ == '__main__':
    main()
