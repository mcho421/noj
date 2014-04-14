#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from sqlalchemy import create_engine
from puremvc.patterns.facade import Facade
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from noj.model import (db, db_constants, models)
from noj.model.profiles import ProfileManager
from noj import controller
from noj.view.lookup_gui import LookupGUI

from noj.model.models import (
    Session, 
    Base,
)

class AppFacade(Facade):

    STARTUP = "STARTUP"
    LOOKUP = "LOOKUP"
    LOOKUP_DONE = "LOOKUP_DONE"
    ENTRY_LOOKUP_DONE = "ENTRY_LOOKUP_DONE"
    EXPRESSION_LOOKUP_DONE = "EXPRESSION_LOOKUP_DONE"

    @staticmethod
    def getInstance():
        return AppFacade()

    def initializeController(self):
        super(AppFacade, self).initializeController()

        super(AppFacade, self).registerCommand(AppFacade.STARTUP, controller.StartupCommand)
        super(AppFacade, self).registerCommand(AppFacade.LOOKUP, controller.LookupCommand)

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

# from http://www.riverbankcomputing.com/pipermail/pyqt/2009-May/022961.html
def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.
    
    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    import time, cStringIO
    import traceback
    from PyQt4 import QtGui

    separator = '-' * 80
    logFile = "simple.log"
    notice = \
        """An unhandled exception occurred. Please report the problem\n"""\
        """using the error reporting dialog or via email to <%s>.\n"""\
        """A log has been written to "%s".\n\nError information:\n""" % \
        ("yourmail at server.com", logFile)
    versionInfo="0.0.1"
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")
    
    
    tbinfofile = cStringIO.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s' % (str(excType), str(excValue))
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    try:
        f = open(logFile, "w")
        f.write(msg)
        f.write(versionInfo)
        f.close()
    except IOError:
        pass
    errorbox = QtGui.QMessageBox()
    errorbox.setText(str(notice)+str(msg)+str(versionInfo))
    errorbox.exec_()

sys.excepthook = excepthook

def main():
    # maybe convert_unicode=True?
    # engine = create_engine('sqlite:///:memory:', echo=True)
    pm = ProfileManager()
    # engine = create_engine('sqlite:///../test.sqlite', echo=True)
    engine = create_engine(pm.database_connect_string(), echo=False)
    print pm.database_connect_string()
    init_db(engine)
    app = AppFacade.getInstance()
    app.registerProxy(pm)

    app_gui = QApplication(sys.argv)
    widget = LookupGUI()
    widget.show()
    app.sendNotification(AppFacade.STARTUP, widget)
    app_gui.exec_()

if __name__ == '__main__':
    main()