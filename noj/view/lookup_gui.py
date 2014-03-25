#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

stylesheet = """\
* {
	font-family:Meiryo, Osaka, Hiragino Kaku Gothic Pro;
}
"""

class LookupGUI(QWidget):
	def __init__(self, parent=None):
		super(LookupGUI, self).__init__(parent)
		self.search_bar = QLineEdit()
		self.search_results = QTextEdit()
		layout = QVBoxLayout()
		layout.addWidget(self.search_bar)
		layout.addWidget(self.search_results)
		self.setLayout(layout)
		self.mediator = None
		self.search_results.setStyleSheet(stylesheet)

	def set_mediator(self, mediator):
		self.mediator = mediator

def main():
	app = QApplication(sys.argv)
	widget = LookupGUI()
	widget.show()
	app.exec_()

if __name__ == '__main__':
	main()