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
        return [noj.AppFacade.LOOKUP_DONE, 
                noj.AppFacade.ENTRY_LOOKUP_DONE,
                noj.AppFacade.EXPRESSION_LOOKUP_DONE,
               ] # AppFacade properties here

    def handleNotification(self, notification):
        if notification.getName() == noj.AppFacade.LOOKUP_DONE:
            ues = notification.getBody()
            print 'lookup done'
            self.viewComponent.search_results.append('<h1>==== ENTRY LOOKUP ====</h1>')
            self.viewComponent.search_results.append(unicode(ues))
        elif notification.getName() == noj.AppFacade.ENTRY_LOOKUP_DONE:
            entries = notification.getBody()
            print 'entry lookup done'
            self.viewComponent.search_results.append('<h1>==== ENTRIES ====</h1>')
            self.viewComponent.search_results.append(unicode(entries.to_html()))
        elif notification.getName() == noj.AppFacade.EXPRESSION_LOOKUP_DONE:
            ues = notification.getBody()
            print 'expression lookup done'
            self.viewComponent.search_results.append('<h1>==== EXPRESSIONS ====</h1>')
            self.viewComponent.search_results.append(unicode(ues))

    def prepareForSearch(self):
        self.viewComponent.search_results.clear()
        # self.viewComponent.search_results.append('Searching...')


    def onSearch(self):
        self.viewComponent.search_bar.selectAll()
        text = unicode(self.viewComponent.search_bar.text())
        self.sendNotification(noj.AppFacade.LOOKUP, text)

    def test(self):
        print 'doing a test'
        self.viewComponent.search_results.setText('test')

