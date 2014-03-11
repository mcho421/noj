#!/usr/bin/env python
# -*- coding: utf-8 -*-
from puremvc.patterns.command import SimpleCommand
from puremvc.interfaces import ICommand
from noj.view.lookup_mediator import LookupMediator
from noj.model.async_lookup import AsyncLookup

class StartupCommand(SimpleCommand, ICommand):
	def execute(self, notification):
		print "executing startup command"
		app_gui = notification.getBody()
		self.facade.registerMediator(LookupMediator(app_gui))
		self.facade.registerProxy(AsyncLookup())

