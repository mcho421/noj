#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from noj.tools.check_platform import isWin, isMac
from PyQt4.QtGui import QDesktopServices

class ProfileManager(object):
    """docstring for ProfileManager"""
    def __init__(self, base=None):
        super(ProfileManager, self).__init__()
        if base:
            self.base = os.path.abspath(base)
        else:
            self.base = self._default_base()
        self.database_file = 'database.sqlite'
        self.ensure_base_exists()
        self.ensure_media_exists()

    def ensure_base_exists(self):
        if not os.path.exists(self.base):
            os.makedirs(self.base)

    def ensure_media_exists(self):
        media_path = self.media_path()
        if not os.path.exists(media_path):
            os.makedirs(media_path)

    def _default_base(self):
        if isWin:
            loc = QDesktopServices.storageLocation(QDesktopServices.DocumentsLocation)
            return os.path.join(unicode(loc), "Natural Order Japanese")
        elif isMac:
            return os.path.expanduser("~/Documents/Natural Order Japanese")
        else:
            return os.path.expanduser("~/Natural Order Japanese")

    def database_connect_string(self):
        abspath = os.path.join(self.base, self.database_file)
        return 'sqlite:///' + abspath

    def media_path(self):
        return os.path.join(self.base, 'media')

        