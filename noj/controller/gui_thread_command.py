#!/usr/bin/env python
# -*- coding: utf-8 -*-
from puremvc.patterns.command import SimpleCommand
from puremvc.interfaces import ICommand
from noj.view.lookup_mediator import LookupMediator
from noj.model.async_lookup import AsyncLookup
from functools import partial
import noj

class GuiThreadCommand(SimpleCommand, ICommand):
	def execute(self, notification):
		print 'executing GUI thread command'
		import threading
		print threading.current_thread()
		callback = notification.getBody()
		noj.AppFacade.getInstance().executeInGuiThread(notification)
		print 'GUI thread command done'

