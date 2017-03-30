from estnltk.vabamorf.morf import Vabamorf
from estnltk.rewriting.syntax_preprocessing.syntax_preprocessing import PronounTypeRewriter

        
class MorphAnalyzedToken():
    def __init__(self, token: str) -> None:
        self.text = token

    def __eq__(self, other):
        if isinstance(other, str):
            return self.text == other
        if isinstance(other, MorphAnalyzedToken):
            return self.text == other.text
        return False

    def __contains__(self, s):
        return s in self.text

    def __len__(self):
        return len(self.text)

    def __str__(self):
        return self.text

    def __repr__(self):
        return "MorphAnalyzedToken('{}')".format(self.text)

    def _replace(self, *args):
        result = self.text.replace(*args)
        if result == self.text:
            return self
        return MorphAnalyzedToken(result)

    def _split(self, *args):
        parts = self.text.split(*args)
        if len(parts) == 1:
            return [self]
        return [MorphAnalyzedToken(part) for part in parts]

    def _isalpha(self):
        return self.text.isalpha()
    
    _analyze = Vabamorf.instance().analyze
    _pronoun_lemmas = set(PronounTypeRewriter.load_pronoun_types())

    @property
    def _analysis(self):
        return MorphAnalyzedToken._analyze([self.text],
                             guess=False,
                             propername=False,
                             disambiguate=False)[0]['analysis']

    @property
    def _part_of_speeches(self):
        return {a['partofspeech'] for a in self._analysis}

    def _lemmas(self, pos=None):
        if pos:
            return {a['lemma'] for a in self._analysis if a['partofspeech']==pos}
        return {a['lemma'] for a in self._analysis}
    
    _all_cases = frozenset({'ab', 'abl', 'ad', 'adt', 'all', 'el', 'es', 'g',
                        'ill','in', 'kom', 'n', 'p', 'ter', 'tr', 'adt_or_ill'})
    
    def _cases(self, pos=None):
        result = set()
        for a in self._analysis:
            if pos:
                if a['partofspeech'] == pos:
                    result.update((a['form']).split())
            else:
                result.update((a['form']).split())
        if {'adt', 'ill'} & result:
            result.add('adt_or_ill')
        return result & MorphAnalyzedToken.all_cases
    
    @property
    def is_word(self):
        return any(a['partofspeech'] not in {'Y', 'Z'} for a in self._analysis)

    @property
    def _is_word_conservative(self):
        if '-' not in self:
            return self.is_word

        syllables = frozenset({'ta','te', 'ma', 'va', 'de', 'me', 'ka', 'sa',
                               'su', 'mu', 'ju', 'era', 'eri', 'eks', 'all',
                               'esi', 'oma', 'ees'})
        parts = self._split('-')
        if parts[0].text in syllables:
            return False
        if self.is_word:
            return all(part.is_word for part in parts)
        return False

    @property
    def is_conjunction(self):
        return any(a['partofspeech']=='J' for a in self._analysis)

    @property
    def _is_simple_pronoun(self):
        '''dok kõigi is meetodite kohta'''
        return bool(MorphAnalyzedToken._pronoun_lemmas & self._lemmas('P'))
    
    @property
    def is_pronoun(self):
        '''dok'''
        if self.normal._is_simple_pronoun:
            return True
        if '-' in self.normal:
            parts = self.normal._split('-')
            if not parts[-1]._is_simple_pronoun:
                return False
            if any('teadma' in part.lemmas() for part in parts):
                return True

            cases = MorphAnalyzedToken.all_cases
            for part in parts:
                if part._is_simple_pronoun:
                    cases &= part.cases('P')
                elif not part.is_conjunction:
                    return False
            if cases:
                return True

            if parts[-1].cases('P') in {'ter', 'es', 'ab', 'kom'}:
                for part in parts[:-1]:
                    if part._is_simple_pronoun and 'g' not in part.cases('P'):
                        return False
                    elif not part.is_conjunction:
                        return False
            return True            
        return False

    def _remove_stammer(self, max_stammer_length=2):
        if '-' not in self or not max_stammer_length:
            return self
        parts = self.text.split('-')
        
        removed = False
        while len(parts) > 1:
            if len(parts[0]) > max_stammer_length:
                break
            if parts[1].startswith(parts[0]):
                del parts[0]
                removed = True
            else:
                break
        if len(parts[0]) < 3:
            return self
        if removed:
            return MorphAnalyzedToken('-'.join(parts))
        return self


    @property
    def _remove_hyphens_smart(self):
        if '-' not in self:
            return self
        parts = self.text.split('-')

        for i in range(len(parts)-1, 0, -1):
            if len(parts[i-1]) > 0 and len(parts[i]) > 0:
                if parts[i-1][-1] == parts[i][0]:
                    if (len(parts[i-1]) > 1 and parts[i-1][-2] == parts[i-1][-1]
                        or len(parts[i]) > 1 and parts[i][0] == parts[i][1]):
                        parts.insert(i,'-')
        token = ''.join(parts)
        if self == token:
            return self
        return MorphAnalyzedToken(token)

    @property
    def normal(self):
        if '-' not in self:
            return self

        if not self._replace('-', '')._isalpha():
            return self

        result1 = self._remove_stammer()
        if result1._is_word_conservative:
            return result1
        result2 = result1._remove_hyphens_smart
        if result2._is_word_conservative:
            return result2

        result3 = result2._replace('-', '')
        if result3.is_word:
            return result3

        if result1._is_word_conservative:
            return result1

        return self