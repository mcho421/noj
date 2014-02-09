#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from noj.misc.uni_printer import UniPrinter
from jcconv import kata2hira

KANA_BOUNDARY_PATTERN = re.compile(ur'[ぁ-ん](?=[ァ-ンー])|[ァ-ンー](?=[ぁ-ん])')

def unformat_jj1_kana(kana_text):
    translation_table = dict.fromkeys(map(ord, u'-・∘'), None)
    # return kata2hira(kana_text.translate(translation_table))
    return kana_text.translate(translation_table)

def add_hyphen_after(match):
    return match.group()[0] + u'-'

def unformat_jj1_kanji(kanji_text, kana_text):
    try:
        hyphened = KANA_BOUNDARY_PATTERN.sub(add_hyphen_after, kana_text)
        kana_comp = hyphened.split(u'-')
        unformat_kanji_comp = list()
        replace_part_idx = 0
        IN_KANJI = 0
        IN_DASH = 1
        last_state = IN_KANJI
        for i, char in enumerate(kanji_text):
            if char == u'―':
                if i != 0:
                    replace_part_idx += 1
                unformat_kanji_comp.append(kana_comp[replace_part_idx])
                last_state = IN_DASH
            else:
                if last_state == IN_DASH:
                    replace_part_idx += 1
                unformat_kanji_comp.append(char)
                last_state = IN_KANJI
        replace_part_idx += 1
        if replace_part_idx > len(kana_comp):
            raise Exception("Error when unformatting kanji {} {}".format(
                replace_part_idx, len(kana_comp)))
        return u''.join(unformat_kanji_comp)
    except Exception as e:
        return kanji_text

def test_unformat():
    lines = [(u'あいあい-し・い', (u'愛愛しい',)),
             (u'あい-いれ∘ない', (u'相容れない',)),
             (u'アッカーマン-きこう', (u'―機構',)),
             (u'あっしゅく-ガス', (u'圧縮―',)),
             (u'あと-ガス', (u'後―', u'跡―',)),
             (u'あか-パンかび', (u'赤―黴',)),
             (u'うちモンゴル-じちく', (u'内―自治区',)),
             (u'しゅつエジプトき', (u'出―記',)),
             ]
    for kana_line, kanji_list in lines:
        print 'kana', kana_line, '--', unformat_jj1_kana(kana_line)
        for kanji_line in kanji_list:
            print 'kanji', kanji_line, '--', unformat_jj1_kanji(kanji_line, kana_line)

def test_unformat_all():
    lines = [(u'あいあい-し・い', (u'愛愛しい',)),
             (u'あい-いれ∘ない', (u'相容れない',)),
             (u'アッカーマン-きこう', (u'―機構',)),
             (u'あっしゅく-ガス', (u'圧縮―',)),
             (u'あと-ガス', (u'後―', u'跡―',)),
             (u'あか-パンかび', (u'赤―黴',)),
             (u'うちモンゴル-じちく', (u'内―自治区',)),
             (u'しゅつエジプトき', (u'出―記',)),
             ]
    import codecs
    errors = codecs.open('errors', 'w', 'utf-8')
    with codecs.open('../converters/daijirin2_kana_kanji', 'r', 'utf-8-sig') as f:
        i = 1
        for line in f:
            if i % 1000 == 0:
                print i
            if i > 84000:
                line = line.strip()
                # line = line.encode('unicode-escape')
                # print type(line), line
                # print line
                tup = eval(line)
                try:
                    kana_line, kanji_list = tup
                    print 'kana', kana_line, '--', unformat_jj1_kana(kana_line)
                    for kanji_line in kanji_list:
                        print 'kanji', kanji_line, '--', unformat_jj1_kanji(kanji_line, kana_line)
                except Exception as e:
                    errors.write(line)

            i += 1

def main():
    test_unformat()
    # test_unformat_all()

if __name__ == '__main__':
    main()
