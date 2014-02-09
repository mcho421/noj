#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from noj import db
from noj import db_constants
from noj import models
from noj.profiles import ProfileManager

from noj.models import (
    Session, 
    Base,
)

def init_db(engine):
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)
    session = Session()

    # Insert library types
    for lib_type, lib_type_id in db_constants.LIB_TYPES_TO_ID.items():
        db.insert(session, models.LibraryType, name=lib_type, id=lib_type_id)

    # Insert usage example list types
    for ue_list_type, ue_list_type_id in db_constants.UE_LIST_TYPES_TO_ID.items():
        db.insert(session, models.UEListType, name=ue_list_type, id=ue_list_type_id)

    # Insert morpheme types
    for mtype, mtype_id in db_constants.MORPHEME_TYPES_TO_ID.items():
        db.insert(session, models.MorphemeType, name=mtype, id=mtype_id)

    # Insert morpheme statuses
    for mstat, mstat_id in db_constants.MORPHEME_STATUSES_TO_ID.items():
        db.insert(session, models.MorphemeStatus, name=mstat, id=mstat_id)

    # Insert known examples list
    db.insert(session, models.UEList, name=db_constants.KNOWN_EXAMPLES_NAME, 
              id=db_constants.KNOWN_EXAMPLES_ID, 
              type_id=db_constants.UE_LIST_TYPES_TO_ID['SYSTEM'])

    session.commit()
    session.close()

def main():
    # maybe convert_unicode=True?
    # engine = create_engine('sqlite:///:memory:', echo=True)
    pm = ProfileManager()
    # engine = create_engine('sqlite:///../test.sqlite', echo=True)
    engine = create_engine(pm.database_connect_string(), echo=True)
    init_db(engine)

if __name__ == '__main__':
    main()