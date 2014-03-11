#!/usr/bin/env python
# -*- coding: utf-8 -*-

LIB_TYPES_TO_ID = {'DICTIONARY': 1,
                   'CORPUS': 2,}

UE_LIST_TYPES_TO_ID = {'USER': 1,
                       'SYSTEM': 2,}

MORPHEME_TYPES_TO_ID = {'INTERJECTION': 1, 
                        'ADVERB': 2, 
                        'PRE_NOUN_ADJECTIVAL': 3, 
                        'NOUN': 4, 
                        'AUXILIARY_VERB': 5,
                        'VERB': 6,
                        'PARTICLE': 7,
                        'PREFIX': 8,
                        'ADJECTIVE': 9,
                        'CONJUNCTION': 10,
                        'FILLER': 11,
                        'SYMBOL': 12,
                        'OTHER': 13,
                        'KANJI_ENTRY': 14,
                        'KANA_ENTRY': 15,}

MORPHEME_STATUSES_TO_ID = {'AUTO': 1,
                           'UNKNOWN': 2,
                           'KNOWN': 3}
KNOWN_EXAMPLES_ID = 1
KNOWN_EXAMPLES_NAME = "Known Examples"

ID_TO_LIB_TYPES = {value: key for key, value in LIB_TYPES_TO_ID.items()}
ID_TO_UE_LIST_TYPES = {value: key for key, value in UE_LIST_TYPES_TO_ID.items()}
ID_TO_MORPHEME_TYPES = {value: key for key, value in MORPHEME_TYPES_TO_ID.items()}
ID_TO_MORPHEME_STATUSES = {value: key for key, value in MORPHEME_STATUSES_TO_ID.items()}
