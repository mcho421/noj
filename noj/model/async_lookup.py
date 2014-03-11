#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from functools import partial
from puremvc.patterns.proxy import Proxy
from multiprocessing.pool import ThreadPool
from noj.model.lookup_ues import LookupUEs
from noj.model.models import Session
import noj


class AsyncLookup(Proxy, QObject):
    NAME = 'AsyncLookup'

    def __init__(self):
        super(AsyncLookup, self).__init__()
        QObject.__init__(self, parent=None)
        # self.pool = ThreadPool()

    def lookup_entries(self, search_word, limit=None, offset=None, callback=None):
        print "looking up entries..."
        pass

    def lookup_ues_by_entry(self, search_word, limit=None, offset=None, callback=None):
        print "looking up ues by entries..."
        # result = self.pool.apply_async(_lookup_ues_by_entry, (search_word, limit, offset, callback),
        #     callback=partial(self.sendNotification, noj.AppFacade.LOOKUP_DONE))
        # result = self.pool.apply_async(_lookup_ues_by_entry, (search_word, limit, offset, callback))
        self.worker = AsyncLookupWorker(search_word, limit, offset, callback)
        self.connect(self.worker, SIGNAL("searchFinished"), self.done_ues_by_entry)
        self.worker.start()
        # result.get()

        # return result
        return None

    def done_ues_by_entry(self, ues):
        print ues
        import threading
        print threading.current_thread()
        self.sendNotification(noj.AppFacade.LOOKUP_DONE, ues)
        # TODO: disconnect

    def lookup_ues_by_definition(self, search_word, limit=None, offset=None, callback=None):
        print "looking up ues by definitions..."
        pass

    def lookup_ues_by_expression(self, search_word, limit=None, offset=None, callback=None):
        print "looking up ues by expressions..."
        pass

class AsyncLookupWorker(QThread):
    """docstring for AsyncLookupWorker"""
    def __init__(self, search_word, limit, offset, callback, parent=None):
        super(AsyncLookupWorker, self).__init__(parent)
        self.search_word = search_word
        self.limit = limit
        self.offset = offset
        self.callback = callback

    def run(self):
        session = Session()
        ues = LookupUEs.lookup_ues_by_entry(session, self.search_word, self.limit, self.offset)
        # print unicode(ues)
        unicode(ues)
        if self.callback is not None:
            self.callback(ues)
        session.close()
        print 'finished searching:', self.search_word
        self.emit(SIGNAL("searchFinished"), ues)
        # return ues
        

def _lookup_ues_by_entry(search_word, limit, offset, callback):
    session = Session()
    ues = LookupUEs.lookup_ues_by_entry(session, search_word, limit, offset)
    # print unicode(ues)
    unicode(ues)
    if callback is not None:
        callback(ues)
    session.close()
    print 'finished searching:', search_word
    return ues


def main():
    import sys
    import logging
    from sqlalchemy import create_engine
    from noj import init_db
    from noj.model.profiles import ProfileManager

    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    pm = ProfileManager()
    pm.database_file = 'jmdict.sqlite'
    # pm.database_file = 'daijirin2.sqlite'
    print pm.database_connect_string()

    search_word = u'面白い'
    # search_word = u'先生'
    # search_word = u'悪どい'
    # search_word = u'スポーツ'
    # search_word = u'生く'

    if len(sys.argv) == 2:
        print sys.getdefaultencoding()
        search_word = sys.argv[1].decode(sys.stdin.encoding)

    engine = create_engine(pm.database_connect_string(), echo=True)
    init_db(engine)
    
    session = Session()
    lookup = AsyncLookup()
    # ues = _lookup_ues_by_entry(search_word, 100, None, None)
    # print unicode(ues)
    result = lookup.lookup_ues_by_entry(search_word, limit=100)
    print 'waiting for results'
    ues = result.get()
    session.close()


if __name__ == '__main__':
    main()
