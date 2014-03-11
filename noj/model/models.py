#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
import json

from sqlalchemy.orm import (
    sessionmaker, 
    scoped_session,
    relationship, 
    reconstructor,
    backref,
)

from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    ForeignKey, 
    Table
)

from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
Session = scoped_session(sessionmaker()) # engine is binded later
# Session = sessionmaker()

class Library(Base):
    """Represents a Usage Example Library."""

    __tablename__ = 'libraries'

    id              = Column(Integer, primary_key=True)
    name            = Column(String, nullable=False)
    alias           = Column(String)
    date            = Column(String)
    dump_version    = Column(String)
    convert_version = Column(String)
    import_version  = Column(String)
    extra           = Column(String)
    type_id         = Column(Integer, ForeignKey('librarytypes.id'), nullable=False)

    lib_type = relationship('LibraryType', backref='libraries')

    unique_fields = []

    def __repr__(self):
        return "<Library({!r})>".format(self.name)

    def breadcrumb_string(self):
        return self.name

class LibraryType(Base):
    """Represents a Usage Example Library Type"""

    __tablename__ = 'librarytypes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    unique_fields = ['name']

    def __repr__(self):
        return "<LibraryType(%s)>" % (self.name)

class EntryHasKanji(Base):
    __tablename__ = 'entryhaskanji'

    entry_id = Column(Integer, ForeignKey('entries.id'), primary_key=True)
    kanji_id = Column(Integer, ForeignKey('morphemes.id'), primary_key=True)
    number = Column(Integer)

    entry = relationship('Entry', backref='kanji_assocs')
    kanji   = relationship('Morpheme', backref='entry_assocs_on_kanji')

    def __repr__(self):
        return "<EntryHasKanji('{!r}, {!r}, {!r}')>".format(self.entry, self.kanji, self.number)

    def __lt__(self, other):
        return self.sorting_key() < other.sorting_key()

    def sorting_key(self):
        is_set_key = 1 if self.number is not None else 2
        number_key = self.number if self.number is not None else 1
        id_key = self.kanji_id
        return (is_set_key, number_key, id_key)

class EntryHasKana(Base):
    __tablename__ = 'entryhaskana'

    entry_id = Column(Integer, ForeignKey('entries.id'), primary_key=True)
    kana_id = Column(Integer, ForeignKey('morphemes.id'), primary_key=True)
    number = Column(Integer)

    entry = relationship('Entry', backref='kana_assocs')
    kana   = relationship('Morpheme', backref='entry_assocs_on_kana')

    def __repr__(self):
        return "<EntryHasKana('{!r}, {!r}, {!r}')>".format(self.entry, self.kana, self.number)

    def __lt__(self, other):
        return self.sorting_key() < other.sorting_key()

    def sorting_key(self):
        is_set_key = 1 if self.number is not None else 2
        number_key = self.number if self.number is not None else 1
        id_key = self.kana_id
        return (is_set_key, number_key, id_key)

class Entry(Base):
    """Represents a dictionary entry."""

    __tablename__ = 'entries'

    id         = Column(Integer, primary_key=True)
    number     = Column(Integer)
    kana_raw   = Column(String)
    kanji_raw  = Column(String)
    accent     = Column(String)
    extra      = Column(String)
    library_id = Column(Integer, ForeignKey('libraries.id'), nullable=False)
    # kana_id    = Column(Integer, ForeignKey('morphemes.id'), nullable=False)
    format_id  = Column(Integer, ForeignKey('entryformats.id'), nullable=False)

    library = relationship('Library', backref='entries')
    # kana    = relationship('Morpheme', backref='entries_from_kana')
    # kana   = relationship('Morpheme', secondary=entry_has_kana, backref='entries_from_kana')
    # kanji   = relationship('Morpheme', secondary=entry_has_kanji, backref='entries_from_kanji')
    format  = relationship('EntryFormat', backref='entries')

    unique_fields = []

    def __repr__(self):
        return "<Entry({!r}, {!r}, {!r}, {!r})>".format(self.kana_assocs, self.kanji_assocs, self.number, self.library)

    def breadcrumb_string(self):
        kana_string = ''
        try:
            kanas = json.loads(self.kana_raw)
        except Exception as e:
            kanas = [k.kana.breadcrumb_string() for k in sorted(self.kana_assocs)]
        if kanas:
            kana_string = u'・'.join(kanas)
        kanji_string = ''
        try:
            kanjis = json.loads(self.kanji_raw)
        except Exception as e:
            kanjis = [k.kanji.breadcrumb_string() for k in sorted(self.kanji_assocs)]
        if kanjis:
            kanji_string = '[' + u'・'.join(kanjis) + ']'
        return kana_string + kanji_string

class EntryFormat(Base):
    """Represents a dictionary format."""

    __tablename__ = 'entryformats'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    unique_fields = ['name']

    def __repr__(self):
        return "<EntryFormat(%s)>" % (self.name)

class DefinitionHasUEs(Base):
    __tablename__ = 'definitionhasues'

    usage_example_id = Column(Integer, ForeignKey('usageexamples.id'), primary_key=True)
    definition_id    = Column(Integer, ForeignKey('definitions.id'), primary_key=True, index=True)
    number           = Column(Integer)
    # really need index on this for create index dhu_idx on definitionhasues(definition_id);

    definition    = relationship('Definition', backref='ue_assocs')
    usage_example = relationship('UsageExample', backref='definition_assocs')

    def __repr__(self):
        return "<DefinitionHasUEs('{!r}, {!r}, {!r}')>".format(self.definitions, self.usage_examples, self.number)

class Definition(Base):
    """Represents a dictionary definition."""

    __tablename__ = 'definitions'

    id          = Column(Integer, primary_key=True)
    definition  = Column(String)
    number      = Column(Integer)
    group       = Column(String)
    extra       = Column(String)
    entry_id    = Column(Integer, ForeignKey('entries.id'), nullable=False)
    # ^ need an index on this
    parent_id   = Column(Integer, ForeignKey('definitions.id'))

    entry = relationship('Entry', backref='definition')
    children = relationship("Definition", backref=backref('parent', remote_side=[id]))

    def __repr__(self):
        return "<Definition({!r})>".format(self.definition)

    def breadcrumb_string(self):
        number_string = ''
        if self.number is not None:
            number_string = '({}) '.format(self.number)
        definition = self.definition or '(No definition)'
        definition = definition.strip().replace('\n', ' ')
        return u'{}{}'.format(number_string, definition)

    def ancestry(self):
        ancestor_list = list()
        curr = self
        ancestor_list.append(curr)
        while curr.parent is not None:
            curr = curr.parent
            ancestor_list.append(curr)
        return reversed(ancestor_list)

class Expression(Base):
    """Represents a Japanese Expression."""

    __tablename__ = 'expressions'

    id         = Column(Integer, primary_key=True)
    expression = Column(String, nullable=False, unique=True)

    unique_fields = ['expression']

    def __repr__(self):
        return "<Expression({!r})>".format(self.expression)

class UsageExample(Base):
    """Represents a usage example."""

    __tablename__ = 'usageexamples'

    id            = Column(Integer, primary_key=True)
    expression_id = Column(Integer, ForeignKey('expressions.id'), nullable=False)
    library_id    = Column(Integer, ForeignKey('libraries.id'), nullable=False)
    type_id       = Column(Integer, ForeignKey('uetypes.id'), nullable=False)
    meaning       = Column(String)
    reading       = Column(String)
    sound         = Column(String)
    image         = Column(String)
    extra         = Column(String)
    is_validated  = Column(Integer, nullable=False, default=1)

    expression = relationship('Expression', backref='usage_examples')
    library    = relationship('Library', backref='usage_examples')

    __table_args__ = (UniqueConstraint('library_id', 'expression_id', name='_library_expression_uc'),
                     )

    unique_fields = ['library_id', 'expression_id']

    @reconstructor
    def init_on_load(self):
        self.n_score = None

    def __repr__(self):
        return "<UsageExample({!r}, {!r})>".format(self.expression, self.meaning)

    def get_expression_score(self):
        if self.n_score is None:
            plus_n = len(self.expression.expression)/100
            for ma in self.expression.morpheme_assocs:
                m = ma.morpheme
                m_count = m.expr_count or 0
                if m_count < 3:
                    plus_n += (3 - m_count)/3
            self.n_score = plus_n
        return self.n_score

    def get_definition_score(self):
        pass

    def get_n_score(self):
        # Update for def_count
        return self.get_expression_score()

class UEType(Base):
    """Represents a usage example type"""

    __tablename__ = 'uetypes'

    id      = Column(Integer, primary_key=True)
    name    = Column(String, nullable=False, unique=True)

    unique_fields = ['name']

    def __repr__(self):
        return "<UEType({!r})>".format(self.name)

class MorphemeType(Base):
    """Represents a morpheme type"""

    __tablename__ = 'morphemetypes'

    id      = Column(Integer, primary_key=True)
    name    = Column(String, nullable=False, unique=True)

    unique_fields = ['name']

    def __repr__(self):
        return "<MorphemeType({!r})>".format(self.name)

class MorphemeStatus(Base):
    """Represents a morpheme learning status"""

    __tablename__ = 'morphemestatuses'

    id      = Column(Integer, primary_key=True)
    name    = Column(String, nullable=False, unique=True)

    unique_fields = ['name']

    def __repr__(self):
        return "<MorphemeType({!r})>".format(self.name)

class Morpheme(Base):
    """Represents a morpheme"""

    __tablename__ = 'morphemes'

    id         = Column(Integer, primary_key=True)
    morpheme   = Column(String, nullable=False)
    type_id    = Column(Integer, ForeignKey('morphemetypes.id'), nullable=False)
    status_id  = Column(Integer, ForeignKey('morphemestatuses.id'), nullable=False)
    expr_count = Column(Integer)
    def_count  = Column(Integer)
    extra      = Column(String)

    morpheme_type = relationship('MorphemeType', backref='morphemes')
    status        = relationship('MorphemeStatus', backref='morphemes')

    unique_fields = ['morpheme', 'type_id']

    __table_args__ = (UniqueConstraint('morpheme', 'type_id', name='_morpheme_morpheme_type_uc'),
                     )

    def __repr__(self):
        return "<Morpheme({!r}, {!r}, {!r})>".format(self.morpheme, self.morpheme_type, self.expr_count)

    def breadcrumb_string(self):
        return self.morpheme

class ExpressionConsistsOf(Base):
    """Association object between expression and morphemes."""

    __tablename__ = 'expressionconsistsof'

    expression_id = Column(Integer, ForeignKey('expressions.id'), primary_key=True)
    morpheme_id   = Column(Integer, ForeignKey('morphemes.id'), primary_key=True)
    position      = Column(Integer, nullable=False, primary_key=True)
    word_length   = Column(Integer, nullable=False)
    conjugation   = Column(String, nullable=False)
    reading       = Column(String, nullable=False)

    expression = relationship('Expression', backref='morpheme_assocs')
    morpheme   = relationship('Morpheme', backref='expression_assocs')

    def __repr__(self):
        return "<ExpressionConsistsOf('{!r}, {!r}, {!r}, {!r}')>".format(self.morpheme, self.expression, self.position, self.word_length)

class DefinitionConsistsOf(Base):
    """Association object between definition and morphemes."""

    __tablename__ = 'definitionconsistsof'

    definition_id = Column(Integer, ForeignKey('definitions.id'), primary_key=True)
    morpheme_id   = Column(Integer, ForeignKey('morphemes.id'), primary_key=True)
    position      = Column(Integer, nullable=False, primary_key=True)
    word_length   = Column(Integer, nullable=False)
    conjugation   = Column(String, nullable=False)
    reading       = Column(String, nullable=False)

    definition = relationship('Definition', backref='morpheme_assocs')
    morpheme   = relationship('Morpheme', backref='definition_assocs')

    def __repr__(self):
        return "<DefinitionConsistsOf('{!r}, {!r}, {!r}, {!r}')>".format(self.morpheme, self.definition, self.position, self.word_length)

ue_part_of_list = Table(
    'uepartoflist', Base.metadata,
    Column('ue_list_id', Integer, ForeignKey('uelists.id'), primary_key=True),
    Column('usage_example_id', Integer, ForeignKey('usageexamples.id'), primary_key=True))

class UEList(Base):
    """Represents a list of usage examples"""

    __tablename__ = 'uelists'

    id      = Column(Integer, primary_key=True)
    name    = Column(String, nullable=False)
    type_id = Column(Integer, ForeignKey('uelisttypes.id'), nullable=False)

    list_type = relationship('UEListType', backref='lists')
    usage_examples  = relationship('UsageExample', secondary=ue_part_of_list, backref='ue_lists')

    unique_fields = []

    def __repr__(self):
        return "<UEList('{!r}')>".format(self.name)

class UEListType(Base):
    """Represents a type of usage example list."""

    __tablename__ = 'uelisttypes'

    id      = Column(Integer, primary_key=True)
    name    = Column(String, nullable=False, unique=True)

    unique_fields = ['name']

    def __repr__(self):
        return "<UEListType('{!r}')>".format(self.name)

word_part_of_list = Table(
    'wordpartoflist', Base.metadata,
    Column('word_list_id', Integer, ForeignKey('wordlists.id'), primary_key=True),
    Column('word_id', Integer, ForeignKey('words.id'), primary_key=True))

class Word(Base):
    """Represents a word in a word list."""

    __tablename__ = 'words'

    id   = Column(Integer, primary_key=True)
    word = Column(String, nullable=False)

    unique_fields = []

    def __repr__(self):
        return "<Word({!r}, {!r})>".format(self.word)

class WordList(Base):
    """Represents a list of words"""

    __tablename__ = 'wordlists'

    id      = Column(Integer, primary_key=True)
    name    = Column(String, nullable=False)
    type_id = Column(Integer, ForeignKey('wordlisttypes.id'), nullable=False)

    list_type = relationship('WordListType', backref='lists')
    words = relationship('Word', secondary=word_part_of_list, backref='word_lists')

    unique_fields = []

    def __repr__(self):
        return "<WordList('{!r}')>".format(self.name)

class WordListType(Base):
    """Represents a type of word list."""

    __tablename__ = 'wordlisttypes'

    id      = Column(Integer, primary_key=True)
    name    = Column(String, nullable=False, unique=True)

    unique_fields = ['name']

    def __repr__(self):
        return "<WordListType('{!r}')>".format(self.name)


def main():
    from sqlalchemy import create_engine
    # maybe convert_unicode=True?
    engine = create_engine('sqlite:///:memory:', echo=True)
    # engine = create_engine('sqlite:///test.sqlite', echo=True)
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    main()