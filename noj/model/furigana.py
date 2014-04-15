#!/usr/bin/env python
# -*- coding: utf-8 -*-
from jcconv import kata2hira

class Furigana(object):
	"""docstring for Furigana"""
	def __init__(self, expression):
		super(Furigana, self).__init__()
		self.expression = expression
		self.sorted_furigana_req_list = None

	def _get_req_list(self):
		if self.sorted_furigana_req_list is None:
			assocs = self.expression.morpheme_assocs
			expression = self.expression.expression
			furigana_req_list = [ma for ma in assocs if ma.reading != expression[ma.position:ma.position+ma.word_length] and 
				kata2hira(expression[ma.position:ma.position+ma.word_length]) != ma.reading and
				expression[ma.position:ma.position+ma.word_length] not in u"一二三四五六七八九十０１２３４５６７８９"]

			self.sorted_furigana_req_list = sorted(furigana_req_list, reverse=True, key=lambda ma: ma.position)
		return list(self.sorted_furigana_req_list)

	def _ruby_substring_index(self, conj, reading):
		begin = 0
		while begin < len(conj) and begin < len(reading):
			if conj[begin] != reading[begin]:
				break
			begin += 1

		end1 = len(conj)
		end2 = len(reading)
		while end1 > 0 and end2 > 0:
			if conj[end1-1] != reading[end2-1]:
				break
			end1 -= 1
			end2 -= 1
		return (begin, end1, end2)

	def html_ruby(self):
		expression = self.expression.expression
		sorted_furigana_req_list = self._get_req_list()
		html_parts = list()
		i = 0
		while sorted_furigana_req_list:
			ma = sorted_furigana_req_list.pop()
			if i >= len(expression):
				break
			elif i == ma.position:
				conj = expression[ma.position:ma.position+ma.word_length]

				begin, end1, end2 = self._ruby_substring_index(conj, ma.reading)

				html_parts.append(conj[:begin])
				html_parts.append(u"<ruby>{conj}<rp>（</rp><rt>{read}</rt><rp>）</rp></ruby>".format(conj=conj[begin:end1], read=ma.reading[begin:end2]))
				html_parts.append(conj[end1:])
				i += ma.word_length
			elif i < ma.position:
				html_parts.append(expression[i:ma.position])
				conj = expression[ma.position:ma.position+ma.word_length]

				begin, end1, end2 = self._ruby_substring_index(conj, ma.reading)

				html_parts.append(conj[:begin])
				html_parts.append(u"<ruby>{conj}<rp>（</rp><rt>{read}</rt><rp>）</rp></ruby>".format(conj=conj[begin:end1], read=ma.reading[begin:end2]))
				html_parts.append(conj[end1:])
				i = ma.position + ma.word_length
			else:
				print "Error: furigana mid={} overextends expresssion eid={}".format(ma.morpheme_id, ma.expression_id)
		if i < len(expression):
			html_parts.append(expression[i:len(expression)])

		return u''.join(html_parts)
