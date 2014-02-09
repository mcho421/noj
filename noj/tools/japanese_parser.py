#!/usr/bin/env python
# -*- coding: utf-8 -*-

# code adapted from:
# http://mecab.googlecode.com/svn/trunk/mecab/doc/bindings.html
# https://github.com/dae/ankiplugins/blob/master/japanese/reading.py

import MeCab
import re
from jcconv import *

BOS_EOS = 0
INTERJECTION = 1
ADVERB = 2
PRE_NOUN_ADJECTIVAL = 3
NOUN = 4
AUXILIARY_VERB = 5
VERB = 6
PARTICLE = 7
PREFIX = 8
ADJECTIVE = 9
CONJUNCTION = 10
FILLER = 11
SYMBOL = 12
OTHER = 13

MORPHEME_TYPES = {
    u'BOS/EOS':BOS_EOS,
    u'感動詞':INTERJECTION,
    u'副詞':ADVERB,
    u'連体詞':PRE_NOUN_ADJECTIVAL,
    u'名詞':NOUN,
    u'助動詞':AUXILIARY_VERB,
    u'動詞':VERB,
    u'助詞':PARTICLE,
    u'接頭詞':PREFIX,
    u'形容詞':ADJECTIVE,
    u'接続詞':CONJUNCTION,
    u'フィラー':FILLER,
    u'記号':SYMBOL,
    u'その他':OTHER,
}

class JapaneseParser(object):
    """A MeCab parser to parse japanese sentences into morphemes."""

    def __init__(self, skipTypes=frozenset([BOS_EOS, SYMBOL])):
        super(JapaneseParser, self).__init__()
        self._parser = None
        self.skipTypes = skipTypes

    def parse(self, expression):
        """Parse a Japanese expression into morphemes. 
        
        Args:
            expression: A Unicode string representing a Japanese
                expression.

        Returns:
            An instance of JapaneseParseResults containing the 
            expression parsed into morphemes.
        """
        expression_utf8 = expression.encode('utf-8')
        node = self.parser.parseToNode(expression_utf8)
        results = JapaneseParseResults()
        results.expression_unicode = expression
        results.expression_utf8 = expression_utf8
        position = 0
        while node:
            feature = unicode(node.feature, encoding='utf-8')
            details = re.split(',', feature)
            for d in range(len(details)):
                if details[d] == '*':
                    details[d] = ''
            type_ = MORPHEME_TYPES[details[0]]
            if type_ not in self.skipTypes:
                morpheme = unicode(node.surface, encoding='utf-8')
                utf8_pos = (node.rlength-node.length)+position
                unicode_pos = len(unicode(expression_utf8[0:utf8_pos], encoding='utf-8'))
                morpheme_obj = JapaneseMorpheme(
                    morpheme=morpheme,
                    base=details[-3],
                    reading=kata2hira(details[-2]),
                    length=len(morpheme),
                    position=unicode_pos,
                    type_=type_)
                results.add_morpheme(morpheme_obj)
            position = position + node.rlength
            node = node.next
        return results

    @property
    def parser(self):
        """Get the Japanese parser by lazy instantiation."""
        if not self._parser:
            self._parser = MeCab.Tagger('mecabrc')
        return self._parser

class JapaneseParseResults(object):
    """Contains morphemes from parsing using JapaneseParser."""
    def __init__(self):
        super(JapaneseParseResults, self).__init__()
        self.expression_utf8 = None
        self.expression_unicode = None
        self.morphemes = list()

    def __iter__(self):
        return self.morphemes.__iter__()

    def __len__(self):
        return len(self.morphemes)

    def __repr__(self):
        return repr(self.morphemes)

    def add_morpheme(self, morpheme):
        """Add a morpheme to the parse results."""
        self.morphemes.append(morpheme)

class JapaneseMorpheme(object):
    """Represents a Japanese Morpheme."""
    def __init__(self, morpheme, base=None, reading=None, 
                 length=None, position=None, type_=None):
        super(JapaneseMorpheme, self).__init__()
        self.morpheme = morpheme
        self.base = base
        self.reading = reading
        self.length = length
        self.position = position
        self.type_ = type_

    def __repr__(self):
        return "JapaneseMorpheme({morpheme}, {base}, {reading}, {length}, \
{position}, {type_})".format(morpheme=self.morpheme.encode('unicode-escape'), 
                             base=self.base.encode('unicode-escape'), 
                             reading=self.reading.encode('unicode-escape'), 
                             length=self.length,
                             position=self.position, 
                             type_=self.type_)

        
if __name__ == "__main__":
    from noj.misc.uni_printer import UniPrinter
    pp = UniPrinter(indent=4)
    parser = JapaneseParser()
    # results = parser.parse(u"明日は晴れるかな")
    #results = parser.parse(u"自動 生成されています.")
    #results = parser.parse(u"自動 生成されています.")
    #results = parser.parse(u"今日もしないとね。")
    #results = parser.parse(u'明日は今日よりやや暖かいでしょう.')
    #results = parser.parse(u'プログラムは一部2,000 円だ.')
    #results = parser.parse(u'データは以下のとおりです。')
    #results = parser.parse(u'This is english')
    results = parser.parse(u"　明日は　　晴れるかな")
    for m in results:
        pp.pprint(m)
