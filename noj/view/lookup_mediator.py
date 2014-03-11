#!/usr/bin/env python
# -*- coding: utf-8 -*-

from puremvc.patterns.mediator import Mediator
from puremvc.interfaces import IMediator
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import noj

class LookupMediator(Mediator, IMediator, QObject):
    NAME = 'LookupMediator'

    def __init__(self, viewComponent):
        # super(LookupMediator, self).__init__(LookupMediator.NAME, viewComponent)
        Mediator.__init__(self, LookupMediator.NAME, viewComponent)
        QObject.__init__(self, parent=None)
        viewComponent.connect(viewComponent.search_bar, SIGNAL('returnPressed()'), self.onSearch)
        viewComponent.set_mediator(self)

    def listNotificationInterests(self):
        return [noj.AppFacade.LOOKUP_DONE] # AppFacade properties here

    def handleNotification(self, notification):
        if notification.getName() == noj.AppFacade.LOOKUP_DONE:
            ues = notification.getBody()
            print 'lookup done'
            # self.emit(SIGNAL('foo'), unicode(ues))
            self.viewComponent.search_results.setText(unicode(ues))

    def onSearch(self):
        self.viewComponent.search_bar.selectAll()
        text = unicode(self.viewComponent.search_bar.text())
        self.sendNotification(noj.AppFacade.LOOKUP, text)

    def test(self):
        print 'doing a test'
        self.viewComponent.search_results.setText('test')

