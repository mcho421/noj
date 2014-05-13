#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
import lxml.html
from lxml import etree
from lxml.html.clean import clean_html
import resources

SCRIPT_TAG = """\
$(document).on('copy', function (e) {
    $('rt').css('visibility', 'hidden');
    bridge.onCopy();
    $('rt').css('visibility', 'visible');
    return false;
});
"""

START_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="qrc:/jquery.js"></script>
<script>{}</script>
</head>
<body>
""".format(SCRIPT_TAG)

END_HTML = """\
</body>
</html>
"""


class NOJWebView(QWebView):
    def __init__(self, parent=None):
        super(NOJWebView, self).__init__(parent)
        self.bridge = JavaScriptQtBridge()
        self.connect(self, SIGNAL("loadFinished(bool)"), self._loadFinished)

    def _loadFinished(self):
        # print "attaching JS->Qt bridge"
        self.bridge.view = self
        self.page().mainFrame().addToJavaScriptWindowObject("bridge", self.bridge)

    def htmlTree(self):
        tree = None
        text = self.selectedHtml()
        unitext = unicode(text)
        if unitext != '':
          tree = lxml.html.fromstring(unitext)
          etree.strip_elements(tree, 'rt')
          etree.strip_tags(tree, 'ruby', 'rb')
        return tree

    def startHtml(self):
        return START_HTML

    def endHtml(self):
        return END_HTML

class JavaScriptQtBridge(QObject):
    """JavaScript object with functions to interact with Qt."""
    def __init__(self, parent=None):
        super(JavaScriptQtBridge, self).__init__(parent)
        self.view = None

    @pyqtSlot()
    def onCopy(self):
        # print 'onCopy'
        tree = self.view.htmlTree()
        text = u''
        html = u''
        if tree is not None:
            html = lxml.html.tostring(tree, encoding='unicode')
            tree = clean_html(tree)
            text = tree.text_content()

        mime = QMimeData()
        mime.setText(text)
        mime.setHtml(html)
        QApplication.clipboard().setMimeData(mime)
