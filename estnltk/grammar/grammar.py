# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

import regex as re
from functools import reduce
from itertools import chain
from collections import defaultdict

from .match import Match, concatenate_matches, copy_rename
from .conflictresolver import resolve_using_maximal_coverage


class Symbol(object):
    """Base symbol for the grammar."""

    def __init__(self, name=None):
        self.__name = name

    @property
    def name(self):
        return self.__name

    def annotate(self, text, conflict_resolver=resolve_using_maximal_coverage):
        matches = self.get_matches(text, conflict_resolver=conflict_resolver)
        layers = defaultdict(list)
        for m in matches:
            md = m.dict
            for k, v in md.items():
                layers[k].append(v)
        for k, v in layers.items():
            v.sort()
            text[k] = v
        return text

    def get_matches(self, text, cache=None, conflict_resolver=resolve_using_maximal_coverage):
        """Get the matches of the symbol on given text."""
        is_root_node = False
        if cache is None:
            cache = {}
            is_root_node = True
        if id(self) in cache:
            return cache[id(self)]
        matches = self.get_matches_without_cache(text, cache=cache)
        cache[id(self)] = matches

        # if this is the root node, resolve the matches
        if is_root_node and conflict_resolver is not None:
            return conflict_resolver(matches)
        return matches

    def get_matches_without_cache(self, text, **env):
        raise NotImplementedError('When this method is called for the case class, it indicates a programming error!')


class Regex(Symbol):
    """Regular expression symbol."""

    def __init__(self, pattern, flags=re.UNICODE | re.MULTILINE, name=None):
        super(Regex, self).__init__(name)
        self.__pattern = re.compile(pattern, flags=flags)

    @property
    def pattern(self):
        return self.__pattern

    def get_matches_without_cache(self, text, **env):
        matches = []
        for mo in self.pattern.finditer(text.text):
            start, end = mo.start(), mo.end()
            matches.append(Match(start, end, text.text[start:end], self.name))
        return matches


class IRegex(Regex):
    """Case insensitive regular expression symbol."""

    def __init__(self, pattern, flags=re.UNICODE | re.MULTILINE | re.IGNORECASE, name=None):
        super(IRegex, self).__init__(pattern, flags, name)


class Lemmas(Symbol):

    def __init__(self, *lemmas, **kwargs):
        super(Lemmas, self).__init__(kwargs.get('name'))
        self.__lemmas = lemmas
        self.__pattern = re.compile('\L<lemmas>', lemmas=lemmas, flags=re.UNICODE | re.IGNORECASE)

    @property
    def lemmas(self):
        return self.__lemmas

    @property
    def pattern(self):
        return self.__pattern

    def get_matches_without_cache(self, text, **env):
        matches = []
        lemmas = text.lemma_lists
        spans = text.word_spans
        for word_lemmas, (start, end) in zip(lemmas, spans):
            for word_lemma in word_lemmas:
                if self.pattern.match(word_lemma):
                    matches.append(Match(start, end, text.text[start:end], self.name))
        return matches


class Postags(Symbol):

    def __init__(self, *postags, **kwargs):
        super(Postags, self).__init__(kwargs.get('name'))
        self.__postags = postags
        self.__pattern = re.compile('\L<postags>', postags=postags, flags=re.UNICODE | re.IGNORECASE)

    @property
    def postags(self):
        return self.__postags

    @property
    def pattern(self):
        return self.__pattern

    def get_matches_without_cache(self, text, **env):
        matches = []
        postags = text.postag_lists
        spans = text.word_spans
        for word_postags, (start, end) in zip(postags, spans):
            for word_postag in word_postags:
                if self.pattern.match(word_postag):
                    matches.append(Match(start, end, text.text[start:end], self.name))
        return matches


class Layer(Symbol):

    def __init__(self, layer_name):
        self.__layer_name = layer_name

    @property
    def layer_name(self):
        return self.__layer_name

    def get_matches_without_cache(self, text, **env):
        return [Match(start, end, text.text[start:end], self.name) for start, end in text.spans(self.layer_name)]


class Union(Symbol):

    def __init__(self, *symbols, **kwargs):
        super(Union, self).__init__(kwargs.get('name'))
        self.__symbols = symbols

    @property
    def symbols(self):
        return self.__symbols

    def get_matches_without_cache(self, text, **env):
        symbols_matches = [e.get_matches(text, **env) for e in self.symbols]
        matches = list(sorted(chain(*symbols_matches)))
        # if the union has a name, then name all the matches after this
        if self.name is not None:
            matches = [copy_rename(m, self.name) for m in matches]
        return matches


def concat(matches_a, matches_b, text, name=None):
    i, j = 0, 0
    n, m = len(matches_a), len(matches_b)
    matches = []
    while i < n and j < m:
        a, b = matches_a[i], matches_b[j]
        if a.end == b.start:
            matches.append(concatenate_matches(a, b, text.text, name))
            j += 1
        elif a.end < b.start:
            i += 1
        else:
            j += 1
    return matches


class Concatenation(Symbol):

    def __init__(self, *symbols, **kwargs):
        super(Concatenation, self).__init__(kwargs.get('name'))
        self.__symbols = symbols

    @property
    def symbols(self):
        return self.__symbols

    def get_matches_without_cache(self, text, **env):
        symbol_matches = [e.get_matches(text, **env) for e in self.symbols]
        matches = list(reduce(lambda a, b: concat(a, b, text), symbol_matches))
        if self.name is not None:
            matches = [copy_rename(m, self.name) for m in matches]
        return matches


def allgaps(matches_a, matches_b, text, name=None):
    matches = []
    for a in matches_a:
        for b in matches_b:
            if a.end <= b.start:
                matches.append(concatenate_matches(a, b, text.text, name))
    return matches


class AllGaps(Symbol):

    def __init__(self, *symbols, **kwargs):
        super(AllGaps, self).__init__(kwargs.get('name'))
        self.__symbols = symbols

    @property
    def symbols(self):
        return self.__symbols

    def get_matches_without_cache(self, text, **env):
        symbol_matches = [e.get_matches(text, **env) for e in self.symbols]
        matches = list(reduce(lambda a, b: allgaps(a, b, text), symbol_matches))
        if self.name is not None:
            matches = [copy_rename(m, self.name) for m in matches]
        return matches


def gaps(matches_a, matches_b, text, name=None):
    matches = []
    for a in matches_a:
        for b in matches_b:
            if a.end <= b.start:
                matches.append(concatenate_matches(a, b, text.text, name))
                break
    return matches


class Gaps(Symbol):

    def __init__(self, *symbols, **kwargs):
        super(Gaps, self).__init__(kwargs.get('name'))
        self.__symbols = symbols

    @property
    def symbols(self):
        return self.__symbols

    def get_matches_without_cache(self, text, **env):
        symbol_matches = [e.get_matches(text, **env) for e in self.symbols]
        matches = list(reduce(lambda a, b: gaps(a, b, text), symbol_matches))
        if self.name is not None:
            matches = [copy_rename(m, self.name) for m in matches]
        return matches

