#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy.sql import and_, select, func
import noj.models

def insert_get(session, orm_class, **kwargs):
    new = True
    row = None
    inserter = orm_class.__table__.insert().prefix_with('OR IGNORE')
    r = session.execute(inserter.values(**kwargs))
    id_ = r.inserted_primary_key[0]
    if r.rowcount == 0:
        new = False
        filter_args = [orm_class.__table__.c[f]==kwargs[f] 
                       for f in orm_class.unique_fields]
        s = orm_class.__table__.select(and_(*filter_args))
        row = session.execute(s).fetchone()
        id_ = row.id
    return (id_, new, row)

def insert_or_replace(session, orm_class, **kwargs):
    row = None
    inserter = orm_class.__table__.insert().prefix_with('OR REPLACE')
    r = session.execute(inserter.values(**kwargs))
    id_ = r.inserted_primary_key[0]
    return id_

def insert(session, orm_class, **kwargs):
    id_, new, row = insert_get(session, orm_class, **kwargs)
    return (id_, new)

def insert_orm(session, orm_obj):
    d = dict()
    for c in orm_obj.__table__.columns:
        if c.key in orm_obj.__dict__:
            d[c.key] = orm_obj.__dict__[c.key]
    return insert(session, orm_obj.__class__, **d)

def insert_orm_or_replace(session, orm_obj):
    d = dict()
    for c in orm_obj.__table__.columns:
        if c.key in orm_obj.__dict__:
            d[c.key] = orm_obj.__dict__[c.key]
    return insert_or_replace(session, orm_obj.__class__, **d)

def insert_many(session, orm_class, tuples):
    inserter = orm_class.__table__.insert().prefix_with('OR IGNORE')
    session.execute(inserter, tuples)

def insert_many_core(session, core_class, tuples):
    inserter = core_class.insert().prefix_with('OR IGNORE')
    return session.execute(inserter, tuples)

def insert_expression(session, parser, ue_expression, morpheme_cache):
    expression_id, new_expression = insert(session, models.Expression, 
                                           expression=ue_expression)
    if new_expression:
        results = parser.parse(ue_expression)
        morphemes_in_expression = set() # items are (morpheme, type_id)

        # For bulk inserting the morpheme-expression association tuples
        expression_components = list()  # list of dicts representing fields

        for m in results.components:
            # Insert or get morpheme, (morpheme, type_id) unique
            morpheme_key = (m['base'], m['type'])
            if morpheme_key in morpheme_cache:
                morpheme_id = morpheme_cache[morpheme_key]
                # if morpheme_count is not None and \
                #         morpheme_key not in morphemes_in_expression:
                #     morpheme_count[morpheme_key] += 1
            else:
                morpheme_id, new_morpheme, morpheme = insert_get(session, 
                    models.Morpheme, morpheme=m['base'], type_id=m['type'])
                morpheme_cache[morpheme_key] = morpheme_id
                # if morpheme_count is not None:
                #     if new_morpheme:
                #         morpheme_count[morpheme_key] = 1
                #     else:
                #         morpheme_count[morpheme_key] = \
                #             (morpheme.count or 0) + 1
            # print 'morpheme id:', morpheme_id

            morphemes_in_expression.add(morpheme_key)

            # Bulk insert later
            expression_components.append({'expression_id':expression_id, 
                                          'morpheme_id':morpheme_id, 
                                          'position':m['position'], 
                                          'word_length':m['length']})

        # Bulk insert the morpheme-expression association tuples
        if len(expression_components) > 0:
            insert_many(session, models.ExpressionConsistsOf, 
                             expression_components)
    return expression_id

def stage_morpheme_counts(session, ue_list_id, expression_id, morpheme_count):
    # expressions     = models.Expression.__table__
    usage_examples  = models.UsageExample.__table__
    # ue_lists        = models.UEList.__table__
    expression_consists_of = models.ExpressionConsistsOf.__table__
    morphemes = models.Morpheme.__table__
    ue_part_of_list = models.ue_part_of_list

    s = select([func.count(usage_examples.c.id)], 
        from_obj=[usage_examples.join(ue_part_of_list)],
        whereclause=and_(ue_part_of_list.c.ue_list_id==ue_list_id,
                         usage_examples.c.expression_id==expression_id))
    num_same_expressions = session.execute(s).first()[0]
    if num_same_expressions == 0:
        s = select([morphemes], 
            from_obj=[expression_consists_of.join(morphemes)], 
            whereclause=expression_consists_of.c.expression_id==expression_id)
        for m in session.execute(s):
            if m.id in morpheme_count:
                morpheme_count[m.id] += 1
            else:
                morpheme_count[m.id] = (m.count or 0) + 1

    
