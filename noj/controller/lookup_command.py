#!/usr/bin/env python
# -*- coding: utf-8 -*-
from puremvc.patterns.command import SimpleCommand
from puremvc.interfaces import ICommand
from noj.view.lookup_mediator import LookupMediator
from noj.model.async_lookup import AsyncLookup
from functools import partial
import noj

class LookupCommand(SimpleCommand, ICommand):
	def execute(self, notification):
		print 'executing lookup command'
		search_word = notification.getBody()
		print 'searching:', search_word
		lookup_proxy = self.facade.retrieveProxy(AsyncLookup.NAME)
		lookup_mediator = self.facade.retrieveMediator(LookupMediator.NAME)
		# lookup_callback = lookup_mediator.lookup_done
		lookup_proxy.lookup_ues_by_entry(search_word, limit=50)
		# self.sendNotification(noj.AppFacade.LOOKUP_DONE, None)
		# lookup_mediator.test()
		print 'lookup command done'

