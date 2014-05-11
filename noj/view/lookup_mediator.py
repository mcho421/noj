#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from puremvc.patterns.mediator import Mediator
from puremvc.interfaces import IMediator
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import noj
from noj.model.profiles import ProfileManager
from noj.view.default_lookup_stylesheet import STYLESHEET

class LookupMediator(Mediator, IMediator, QObject):
    NAME = 'LookupMediator'

    def __init__(self, viewComponent):
        Mediator.__init__(self, LookupMediator.NAME, viewComponent)
        QObject.__init__(self, parent=None)
        viewComponent.connect(viewComponent.search_bar, SIGNAL('returnPressed()'), self.onSearch)
        viewComponent.set_mediator(self)

        # Setup stylesheet
        pm = self.facade.retrieveProxy(ProfileManager.NAME)
        settings = self.viewComponent.search_results.settings()
        stylesheet_path = pm.lookup_stylesheet_path()
        if not os.path.isfile(stylesheet_path):
            f = open(stylesheet_path, 'w')
            f.write(STYLESHEET)
            f.close()
        stylesheet_url = QUrl(u'file://' + QDir.fromNativeSeparators(stylesheet_path))
        settings.setUserStyleSheetUrl(stylesheet_url)

        # Setup buffers
        self.html_dictionary_entries = None
        self.html_ues_via_entry = None
        self.html_ues_via_expression = None
    
    def listNotificationInterests(self):
        return [noj.AppFacade.LOOKUP_DONE, 
                noj.AppFacade.ENTRY_LOOKUP_DONE,
                noj.AppFacade.EXPRESSION_LOOKUP_DONE,
               ] # AppFacade properties here

    def handleNotification(self, notification):
        if notification.getName() == noj.AppFacade.LOOKUP_DONE:
            ues = notification.getBody()
            print 'lookup done'
            self.html_ues_via_entry = u'<h1>Examples from Entry</h1>' + unicode(ues.to_html())
            self.update_page()
        elif notification.getName() == noj.AppFacade.ENTRY_LOOKUP_DONE:
            entries = notification.getBody()
            print 'entry lookup done'
            self.html_dictionary_entries = u'<h1>Dictionary Meanings</h1>\n' + unicode(entries.to_html())
            self.update_page()
        elif notification.getName() == noj.AppFacade.EXPRESSION_LOOKUP_DONE:
            ues = notification.getBody()
            print 'expression lookup done'
            self.html_ues_via_expression = u'<h1>Examples from Expression</h1>' + unicode(ues.to_html())
            self.update_page()

    def update_page(self):
        # if scrollbar restore code doesn't work, see:
        # http://stackoverflow.com/questions/17060966/restore-scrollbar-position-of-qwebview-after-sethtml
        scroll_pos = self.viewComponent.search_results.page().mainFrame().scrollBarValue(Qt.Vertical)
        html_buffer = list()
        html_buffer.append(self.viewComponent.search_results.startHtml())
        if self.html_dictionary_entries is not None:
            html_buffer.append(self.html_dictionary_entries)
        if self.html_ues_via_entry is not None:
            html_buffer.append(self.html_ues_via_entry)
        if self.html_ues_via_expression is not None:
            html_buffer.append(self.html_ues_via_expression)
        html_buffer.append(self.viewComponent.search_results.endHtml())
        self.viewComponent.search_results.setHtml(u'\n'.join(html_buffer))
        self.viewComponent.search_results.page().mainFrame().setScrollBarValue(Qt.Vertical, scroll_pos)


    def prepareForSearch(self, search_word):
        self.html_dictionary_entries = None
        self.html_ues_via_entry = None
        self.html_ues_via_expression = None
        self.viewComponent.search_results.setHtml(u'Searching for "{}"...'.format(search_word))


    def onSearch(self):
        self.viewComponent.search_bar.selectAll()
        text = unicode(self.viewComponent.search_bar.text())
        self.sendNotification(noj.AppFacade.LOOKUP, text)

