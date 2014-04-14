#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Furigana(object):
	"""docstring for Furigana"""
	def __init__(self, expression):
		super(Furigana, self).__init__()
		self.expression = expression

	def html_ruby(self):
		assocs = self.expression.morpheme_assocs
		expression = self.expression.expression
		furigana_req_list = [ma for ma in assocs if ma.reading != expression[ma.position:ma.position+ma.word_length]]
		sorted_furigana_req_list = sorted(furigana_req_list, reverse=True, key=lambda ma: ma.position)
		html_parts = list()
		i = 0
		while sorted_furigana_req_list:
			ma = sorted_furigana_req_list.pop()
			if i >= len(expression):
				break
			elif i == ma.position:
				conj = expression[ma.position:ma.position+ma.word_length]

				begin1 = 0
				begin2 = 0
				while begin1 < len(conj) and begin2 < len(ma.reading):
					if conj[begin1] != ma.reading[begin1]:
						break
					begin1 += 1
					begin2 += 1

				end1 = len(conj)
				end2 = len(ma.reading)
				while end1 > 0 and end2 > 0:
					if conj[end1-1] != ma.reading[end2-1]:
						break
					end1 -= 1
					end2 -= 1
				html_parts.append(conj[:begin1])
				html_parts.append(u"<ruby>{conj}<rp>（</rp><rt>{read}</rt><rp>）</rp></ruby>".format(conj=conj[begin1:end1], read=ma.reading[begin2:end2]))
				html_parts.append(conj[end1:])
				i += ma.word_length
			elif i < ma.position:
				html_parts.append(expression[i:ma.position])
				conj = expression[ma.position:ma.position+ma.word_length]

				begin1 = 0
				begin2 = 0
				while begin1 < len(conj) and begin2 < len(ma.reading):
					if conj[begin1] != ma.reading[begin1]:
						break
					begin1 += 1
					begin2 += 1

				end1 = len(conj)
				end2 = len(ma.reading)
				while end1 > 0 and end2 > 0:
					if conj[end1-1] != ma.reading[end2-1]:
						break
					end1 -= 1
					end2 -= 1
				html_parts.append(conj[:begin1])
				html_parts.append(u"<ruby>{conj}<rp>（</rp><rt>{read}</rt><rp>）</rp></ruby>".format(conj=conj[begin1:end1], read=ma.reading[begin2:end2]))
				html_parts.append(conj[end1:])
				i = ma.position + ma.word_length
			else:
				print "Error: furigana mid={} overextends expresssion eid={}".format(ma.morpheme_id, ma.expression_id)
		if i < len(expression):
			html_parts.append(expression[i:len(expression)])

		return u''.join(html_parts)
