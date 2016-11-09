import pytest

from estnltk.legacy.text import Text as OldText
from estnltk.rewriting import RegexRewriter
from estnltk.text import *
#


def test_general():
    t = words_sentences('Minu nimi on Uku. Mis Sinu nimi on? Miks me seda arutame?')

    assert isinstance(t.sentences, SpanList)
    assert isinstance(t.words, SpanList)


    assert len(t.sentences) == 3
    assert len(t.words) == 15
    assert len(t.sentences.words) == 3
    assert t.sentences.words == t.sentences
    with pytest.raises(Exception):
        t.words.sentences

    assert len(t.words) == len(t.words.text)
    assert len(t.sentences) == len(t.sentences.text)
    assert len(t.sentences.words.text) == len(t.sentences.text)
    print(t.morf_analysis.lemma )
    assert t.morf_analysis.lemma == [['mina'], ['nimi'], ['olema', 'olema'], ['Uku'], ['.'], ['mis', 'mis'], ['sina'], ['nimi'], ['olema', 'olema'], ['?'], ['miks'], ['mina'], ['see'], ['arutama'], ['?']]


    assert len(t.morf_analysis.lemma) == len(t.words)
    assert len(t.morf_analysis) == len(t.words)

    print(t.words.morf_analysis)
    print(t.words.lemma)
    assert t.words.morf_analysis.lemma == t.words.lemma
    assert len(t.sentences[1:].words) == len(t.sentences[1:].text)

    print('mrf', (t.sentences[1:].morf_analysis))
    print(t.sentences[1:].text)
    assert len(t.sentences[1:].morf_analysis) == len(t.sentences[1:].text)


    assert len(t.sentences[:].morf_analysis) == len(t.sentences[:].text)
    assert (t.sentences[:]) == (t.sentences)
    assert (t.words[:]) == (t.words)
    assert (t.words[:].lemma) == (t.words.lemma)
    assert (t.words[:].text) == (t.words.text)

def test_new_span_hierarchy():
    text = words_sentences('''
    Lennart Meri "Hõbevalge" on jõudnud rahvusvahelise lugejaskonnani.
    Seni vaid soome keelde tõlgitud teos ilmus äsja ka itaalia keeles
    ning seda esitleti Rooma reisikirjanduse festivalil.
    Tuntud reisikrijanduse festival valis tänavu peakülaliseks Eesti,
    Ultima Thule ning Iidse-Põhjala ja Vahemere endisaegsed kultuurikontaktid j
    ust seetõttu, et eelmisel nädalal avaldas kirjastus Gangemi "Hõbevalge"
    itaalia keeles, vahendas "Aktuaalne kaamera".''')
    l = Layer(
        name='layer1',
        parent='words',
        attributes=['test1']
    )

    text._add_layer(l)

    for i in text.words:
        i.mark('layer1').test1 = '1234'


    l = Layer(
        name='layer2',
        parent='layer1',
        attributes=['test2']
    )
    text._add_layer(l)

    for i in text.layer1:
        i.mark('layer2').test2 = '1234'

    #the parent is now changed to "words"
    #it is confusing, but it stays right now to save me from a rewrite
    assert text.layer2[0].parent.layer.name == 'words'

# def test_spans():
#     text = Text('Mingi tekst')
#     layer = Layer(name='test')
#     text._add_layer(layer)
#     a = Span(1, 2)
#     layer.add_span(a)
#
#
#     assert a.start == 1
#     assert a.end == 2
#     assert a.layer is layer
#
#     # with pytest.raises(AssertionError):
#     #     Span(2, 1)
#     #
#
#     #TODO
#     with pytest.raises(AttributeError):
#         # slots should not allow assignement
#         Span(1, 2).test = 12
#
#     assert Span(1, 2).text == 'i'
#
#     with pytest.raises(AttributeError):
#         # Span text should not be assignable
#         Span(1, 2).text = 'a'
#
#
# #fixed
# def test_span_ordering():
#     text = Text('Mingi tekst')
#     layer = Layer(name='test')
#     text._add_layer(layer)
#     a = Span(1, 2)
#     b = Span(2, 3)
#     c = Span(2, 3)
#
#     layer.add_span(a)
#     layer.add_span(b)
#     layer.add_span(c)
#     assert a < b
#     assert not a > b
#     assert a <= b
#     assert not a >= b
#     assert b > a
#     assert not b < a
#     assert b >= a
#     assert c == b
#     assert not a == b
#
#     # layer2 = Layer(text_object=text, name='test2')
#     # x = Span(1, 2, layer2)
#     # with pytest.raises(AssertionError):
#     #     x == a
#
#
def test_text():
    t = Text('test')
    assert t.text == 'test'
    with pytest.raises(AttributeError):
        t.text = 'asd'
#
#
def test_spanList():
    text = Text('')

    layer = Layer(name='test')
    text._add_layer(layer)
    sl = SpanList(layer=layer)
    span = Span(0, 1)
    sl.add_span(span)

    assert len(sl) == 1
    assert list(sl)[0] is span

    with pytest.raises(TypeError):
        sl['asd']

    # insertion keeps items in sorted order
    sl = SpanList(layer=layer)
    a, b, c, d = [Span(i, i + 1, layer) for i in range(4)]
    sl.add_span(b)
    sl.add_span(c)
    sl.add_span(a)
    sl.add_span(d)
    assert sl[0] == a
    assert sl[1] == b
    assert sl[2] == c
    assert sl[3] == d


#
#
def test_layer():
    text = 'Öösel on kõik kassid hallid.'
    t = Text(text)
    l = Layer(name='test')
    t._add_layer(l)

    with pytest.raises(AssertionError):
        t._add_layer(Layer(name='text'))

    with pytest.raises(AssertionError):
        t._add_layer(Layer(name='test'))

    with pytest.raises(AssertionError):
        t._add_layer(Layer(name=' '))

    with pytest.raises(AssertionError):
        t._add_layer(Layer(name='3'))

    with pytest.raises(AssertionError):
        t._add_layer(Layer(name='assert'))

    with pytest.raises(AssertionError):
        t._add_layer(Layer(name='is'))

    assert t.layers['test'] is l
    assert t.test is l.spans

    with pytest.raises(AttributeError):
        t.notexisting

    assert t.text == text

    layer = t.test  # type: Layer
    layer.add_span(
        Span(start=0, end=2)
    )
    assert t.test.text == [text[:2]]

    t.test.add_span(
        Span(start=2, end=4)
    )

    #TODO:
    #Otsusta, mis peaks juhtuma kattuva SPANi korral.
    # with pytest.raises(AssertionError):
    #     t.test.add_span(
    #         Span(start=2, end=4)
    #     )



#
## "Unbound" is not a concept right now
# def test_unbound_layer():
#     text = 'Öösel on kõik kassid hallid.'
#     t = Text(text)
#
#     l = Layer(name='test')
#
#     l.add_span(Span(1, 2))
#
#     with pytest.raises(AttributeError):
#         for i in l:
#             (i.text)
#
#     t._add_layer(l)
#     #does not raise AttributeError after having been added to text object
#     for i in l:
#         (i.text)



def test_annotated_layer():
    text = 'Öösel on kõik kassid hallid.'
    t = Text(text)
    l = Layer(name='test', attributes=['test', 'asd'])
    t._add_layer(l)
    l.add_span(Span(1, 5))

    for i in t.test:
        i.test = 'mock'

    #TODO: make span attributes fixed
    # with pytest.raises(AttributeError):
    #     for i in t.test:
    #         i.test2 = 'mock'

def test_count_by():
    def count_by(layer, attributes, counter=None):
        from collections import Counter
        if counter is None:
            counter = Counter()

        for span in layer:
            key = []
            for a in attributes:
                if a == 'text':
                    key.append(span.text)
                else:
                    key.append(getattr(span, a))
            key = tuple(key)
            counter[key] += 1

        return counter

    text = 'Öösel on kõik kassid hallid.'
    t = Text(text)
    l = Layer(name='test', attributes=['test', 'asd'])
    t._add_layer(l)
    l.add_span(Span(1, 5))
    l.add_span(Span(2, 6))

    for i in l:
        i.asd = 123
        break

    assert (count_by(l, ['text', 'asd'])) == {('ösel', 123): 1, ('sel ', None): 1}
#

def test_from_dict():
    t = Text('Kui mitu kuud on aastas?')
    words = Layer(name='words', attributes=['lemma'])
    t._add_layer(words)
    words.from_dict([{'end': 3, 'lemma': 'kui', 'start': 0},
                                           {'end': 8, 'lemma': 'mitu', 'start': 4},
                                           {'end': 13, 'lemma': 'kuu', 'start': 9},
                                           {'end': 16, 'lemma': 'olema', 'start': 14},
                                           {'end': 23, 'lemma': 'aasta', 'start': 17},
                                           {'end': 24, 'lemma': '?', 'start': 23}]
                    )

    for span, lemma in zip(t.words, ['kui', 'mitu', 'kuu', 'olema', 'aasta', '?']):
        print(span.lemma, lemma)
        assert span.lemma == lemma

def test_ambiguous_from_dict():
    t = Text('Kui mitu kuud on aastas?')
    words = Layer(name='words', attributes=['lemma'], ambiguous = True)
    t['words'] = words


    words.from_dict([
                     [{'end': 3, 'lemma': 'kui', 'start': 0}, {'end': 3, 'lemma': 'KUU', 'start': 0}] ,
                       [{'end': 8, 'lemma': 'mitu', 'start': 4}],
                       [{'end': 13, 'lemma': 'kuu', 'start': 9}],
                       [{'end': 16, 'lemma': 'olema', 'start': 14}],
                       [{'end': 23, 'lemma': 'aasta', 'start': 17}],
                       [{'end': 24, 'lemma': '?', 'start': 23}]
                       ]
                    )

    assert t.words[0].lemma == ['kui', 'KUU']

def test_ambiguous_from_dict_unbound():
    words = Layer(name='words', attributes=['lemma'], ambiguous = True)

    #We create the layer
    words.from_dict([
                     [{'end': 3, 'lemma': 'kui', 'start': 0}, {'end': 3, 'lemma': 'KUU', 'start': 0}] ,
                       [{'end': 8, 'lemma': 'mitu', 'start': 4}],
                       [{'end': 13, 'lemma': 'kuu', 'start': 9}],
                       [{'end': 16, 'lemma': 'olema', 'start': 14}],
                       [{'end': 23, 'lemma': 'aasta', 'start': 17}],
                       [{'end': 24, 'lemma': '?', 'start': 23}]
                       ]
                    )

    #then we bind it to an object
    t = Text('Kui mitu kuud on aastas?')
    t['words'] = words

    assert t.words[0].lemma == ['kui', 'KUU']


    words2 = Layer(name='words2', attributes=['lemma2'], ambiguous = True, parent='words')
    #We create the layer
    words2.from_dict([
                     [{'end': 3, 'lemma2': 'kui', 'start': 0}, {'end': 3, 'lemma2': 'KUU', 'start': 0}] ,
                       [{'end': 8, 'lemma2': 'mitu', 'start': 4}],
                       [{'end': 13, 'lemma2': 'kuu', 'start': 9}],
                       [{'end': 16, 'lemma2': 'olema', 'start': 14}],
                       [{'end': 23, 'lemma2': 'aasta', 'start': 17}],
                       [{'end': 24, 'lemma2': '?', 'start': 23}]
                       ]
                    )
    t['words2'] = words2
    assert t.words2[0].lemma2 == ['kui', 'KUU']

    assert t.words2[0].parent is t.words[0]

def test_dependant_span():
    t = Text('Kui mitu kuud on aastas?')
    words = Layer(name='words',
                  attributes=['lemma']
                  ).from_dict([{'end': 3, 'lemma': 'kui', 'start': 0},
                                           {'end': 8, 'lemma': 'mitu', 'start': 4},
                                           {'end': 13, 'lemma': 'kuu', 'start': 9},
                                           {'end': 16, 'lemma': 'olema', 'start': 14},
                                           {'end': 23, 'lemma': 'aasta', 'start': 17},
                                           {'end': 24, 'lemma': '?', 'start': 23}],
                                  )
    t._add_layer(words)

    dep = Layer(name='reverse_lemmas',
                   parent='words',
                   attributes=['revlemma']
                   )
    t._add_layer(dep)

    for word in t.words:
        word.mark('reverse_lemmas').revlemma = word.lemma[::-1]

    print(t.layers['words']._base)

    for i in t.reverse_lemmas:
        assert (i.revlemma == i.lemma[::-1])

    #TODO: how should this work?
    # for i in t.words:
    #     assert (i.mark('reverse_lemmas').revlemma == i.lemma[::-1])
#
# def test_delete_layer():
#     t = Text('Kui mitu kuud on aastas?')
#     words = Layer('words', attributes=['lemma']).from_dict([{'end': 3, 'lemma': 'kui', 'start': 0},
#                                            {'end': 8, 'lemma': 'mitu', 'start': 4},
#                                            {'end': 13, 'lemma': 'kuu', 'start': 9},
#                                            {'end': 16, 'lemma': 'olema', 'start': 14},
#                                            {'end': 23, 'lemma': 'aasta', 'start': 17},
#                                            {'end': 24, 'lemma': '?', 'start': 23}]
#                                   )
#     t._add_layer(words)
#
#     assert len(t.layers) == 1
#     del t.words
#     assert len(t.layers) == 0
#
#
#
def test_enveloping_layer():
    t = Text('Kui mitu kuud on aastas?')
    words = Layer(
    name='words',
    attributes = ['lemma']

    ).from_dict([{'end': 3, 'lemma': 'kui', 'start': 0},
                                           {'end': 8, 'lemma': 'mitu', 'start': 4},
                                           {'end': 13, 'lemma': 'kuu', 'start': 9},
                                           {'end': 16, 'lemma': 'olema', 'start': 14},
                                           {'end': 23, 'lemma': 'aasta', 'start': 17},
                                           {'end': 24, 'lemma': '?', 'start': 23}],
                                  )
    t._add_layer(words)
    wordpairs = Layer(name='wordpairs', enveloping='words')
    t._add_layer(wordpairs)

    wordpairs._add_spans_to_enveloping(t.words.spans[0:2])
    wordpairs._add_spans_to_enveloping(t.words.spans[2:4])
    wordpairs._add_spans_to_enveloping(t.words.spans[4:6])

    print(t.wordpairs.text)
    assert (wordpairs.text == [['Kui', 'mitu'], ['kuud', 'on'], ['aastas', '?']])

    wordpairs._add_spans_to_enveloping(t.words.spans[1:3])
    wordpairs._add_spans_to_enveloping(t.words.spans[3:5])
    print(t.wordpairs.text)
    assert (wordpairs.text == [['Kui', 'mitu'], ['mitu', 'kuud'], ['kuud', 'on'], ['on', 'aastas'], ['aastas', '?']])


    for wordpair in t.wordpairs:
        for word in wordpair.words:
            assert (word)


    print(t._g.nodes(), t._g.edges())
    for wordpair in t.wordpairs:
        (wordpair.lemma) #this should not give a keyerror


    #I have changed my mind about what this should raise so much, I'm leaving it free at the moment
    with pytest.raises(Exception):
        for wordpair in t.wordpairs:
            (wordpair.nonsense)  # this SHOULD give a --keyerror--

    assert (t.words.lemma == ['kui', 'mitu', 'kuu', 'olema', 'aasta', '?'])
    print(t.wordpairs.lemma)
    assert (t.wordpairs.lemma == [['kui', 'mitu'], ['mitu', 'kuu'], ['kuu', 'olema'], ['olema', 'aasta'], ['aasta', '?']])

    print(t.wordpairs.text)
    with pytest.raises(Exception):
        (wordpairs.test)
#
def test_oldtext_to_new():

    text = 'Tuleb üks neiuke, järelikult tuleb ühelt poolt! Kui tuleks kaks neiukest, siis tuleksid kahelt poolt! Aga seekord tuleb üks, tuleb ühelt poolt!'
    new = words_sentences(text)
    old = OldText(text)


    for sentence, old_sentence in zip(new.sentences, old.split_by_sentences()):
        assert (sentence.text == [word['text'] for word in old_sentence.words])

    assert (new.sentences.text == [['Tuleb', 'üks', 'neiuke', ',', 'järelikult', 'tuleb', 'ühelt', 'poolt', '!'],
                                   ['Kui', 'tuleks', 'kaks', 'neiukest', ',', 'siis', 'tuleksid', 'kahelt', 'poolt', '!'],
                                   ['Aga', 'seekord', 'tuleb', 'üks', ',', 'tuleb', 'ühelt', 'poolt', '!']])
    assert (new.text == text)
#
#
def test_various():
    text = words_sentences('Minu nimi on Joosep, mis sinu nimi on? Miks me seda arutame?')

    upper = Layer(parent='words',
                           name='uppercase',
                           attributes=['upper'])
    text._add_layer(upper)

    for word in text.words:
        #     print(word.text)
        word.mark('uppercase').upper = word.text.upper()

    with pytest.raises(AttributeError):
        for word in text.words:
            word.nonsense

    for word in text.uppercase:
        assert word.text.upper() == word.upper

    for word in text.words:
        assert (word.upper == word.text.upper())

        #TODO: ban unspecified assignement
        # with pytest.raises(AttributeError):
        #     #but we can't assign this way.
        #     word.upper = 123

        #we have to get explicit access
        #TODO: double marking
        word.mark('uppercase').upper = 'asd'

    # assert text.uppercase.text == text.words.text
    # print(text.uppercase.upper)
    # assert text.uppercase.upper == ['asd' for _ in text.words]
    #
    # for sentence in text.sentences:
    #     print(sentence.words)
    #     print(sentence.upper)
#
#
def test_words_sentences():
    t = words_sentences('Minu nimi on Uku, mis sinu nimi on? Miks me seda arutame?')

    assert t.sentences.text == [['Minu', 'nimi', 'on', 'Uku', ',', 'mis', 'sinu', 'nimi', 'on', '?'], ['Miks', 'me', 'seda', 'arutame', '?']]
    assert t.words.text == ['Minu', 'nimi', 'on', 'Uku', ',', 'mis', 'sinu', 'nimi', 'on', '?', 'Miks', 'me', 'seda', 'arutame', '?']
    assert t.text == 'Minu nimi on Uku, mis sinu nimi on? Miks me seda arutame?'

    assert [sentence.text for sentence in t.sentences] == t.sentences.text

    with pytest.raises(AttributeError):
        t.nonsense

    with pytest.raises(Exception):
        t.sentences.nonsense

    with pytest.raises(Exception):
        t.nonsense.nonsense

    with pytest.raises(Exception):
        t.words.nonsense
#
    dep = Layer(name='uppercase',
                         parent='words',
                         attributes=['upper']
                         )
    t._add_layer(dep)
    for word in t.words:
        word.mark('uppercase').upper = word.text.upper()

    assert t.uppercase.upper == ['MINU', 'NIMI', 'ON', 'UKU', ',', 'MIS', 'SINU', 'NIMI', 'ON', '?', 'MIKS', 'ME', 'SEDA', 'ARUTAME', '?']
    print(t.sentences)
    print(t.sentences.uppercase)

    print(t.sentences.uppercase.upper)
    assert t.sentences.uppercase.upper == [['MINU', 'NIMI', 'ON', 'UKU', ',', 'MIS', 'SINU', 'NIMI', 'ON', '?', ],[ 'MIKS', 'ME', 'SEDA', 'ARUTAME', '?']]

#
#     #TODO
#     # assert t.words.uppercase.upper == ['MINU', 'NIMI', 'ON', 'UKU', ',', 'MIS', 'SINU', 'NIMI', 'ON', '?', 'MIKS', 'ME', 'SEDA', 'ARUTAME', '?']
#

def test_ambiguous_layer():
    t = words_sentences('Minu nimi on Uku, mis sinu nimi on? Miks me seda arutame?')

    dep = Layer(name='test',
                         parent='words',
                         ambiguous=True,
                         attributes=['asd']
                         )
    t._add_layer(dep)

    t.words[0].mark('test').asd = 'asd'
    print('mark', t.words[0], t.words[0].asd)

    t.words[1].mark('test').asd = '123'
    t.words[0].mark('test').asd = '123'

    print(t.test)


    print(t.words[0].asd)
#
# def test_morf():
#     text = words_sentences('Minu nimi on Uku, mis sinu nimi on? Miks me seda arutame?')
#     for i in text.words:
#         i.morf_analysis
#
#
#     text.words.lemma
#
#     text.morf_analysis.lemma
#     assert text.sentences.lemma != text.words.lemma
#     text.sentences[:1].lemma
#     text.sentences[:1].words
#
#     assert len(text.sentences[:1].words.lemma) > 0
#
#     #TODO
#     # text.words[0:2].morf_analysis
#
#
# def test_delete_morf():
#     text = words_sentences('Olnud aeg.')
#     prelen = len(text.words[0].morf_analysis)
#     text.words[0].morf_analysis[0].delete()
#
#     assert len(text.words[0].morf_analysis) == prelen - 1
#

def test_change_lemma():
    text = words_sentences('Olnud aeg.')
    setattr(text.morf_analysis[0][0], 'lemma', 'blabla')
    assert text.morf_analysis[0][0].lemma == 'blabla'

    setattr(text.morf_analysis[0][1], 'lemma', 'blabla2')
    assert text.morf_analysis[0][1].lemma == 'blabla2'

#
# #
#
# def test_rewrite():
#     text = Text('Kui mitu kuud on aastas?')
#
#     words = Layer.from_span_dict('words', [{'end': 3, 'test': 'kui', 'start': 0},
#                                            {'end': 8, 'test': 'mitu', 'start': 4},
#                                            {'end': 13, 'test': 'kuu', 'start': 9},
#                                            {'end': 16, 'test': 'olema', 'start': 14},
#                                            {'end': 23, 'test': 'aasta', 'start': 17},
#                                            {'end': 24, 'test': '?', 'start': 23}],
#                                   attributes=['test']
#                                   )
#     text._add_layer(words)
#     rewriter = RegexRewriter(
#         [('kui', 'siis_kui')]
#     )
#
#     text.words[0].rewrite_attribute('test', rewriter)
#
#     assert text.words[0].test == 'siis_kui'
#
#     rewriter = RegexRewriter(
#         [('.', 'X')]
#     )
#     for i in text.words:
#         i.rewrite_attribute('test', rewriter)
#
#     for i in text.words:
#         assert set(i.test) == set('X')


def test_morf():
    text = words_sentences('''
    Lennart Meri "Hõbevalge" on jõudnud rahvusvahelise lugejaskonnani.
    Seni vaid soome keelde tõlgitud teos ilmus äsja ka itaalia keeles
    ning seda esitleti Rooma reisikirjanduse festivalil.
    Tuntud reisikrijanduse festival valis tänavu peakülaliseks Eesti,
    Ultima Thule ning Iidse-Põhjala ja Vahemere endisaegsed kultuurikontaktid j
    ust seetõttu, et eelmisel nädalal avaldas kirjastus Gangemi "Hõbevalge"
    itaalia keeles, vahendas "Aktuaalne kaamera".''')


    assert len(text.morf_analysis[5]) == 2
    print(text.morf_analysis[5])
    print(text.morf_analysis[5].lemma)
    assert len(text.morf_analysis[5].lemma) == 2
    assert (text.morf_analysis[5].lemma) == ['olema', 'olema']
    assert (text.morf_analysis.lemma == [['Lennart'], ['Meri'], ['"'], ['hõbevalge'], ['"'], ['olema', 'olema'], ['jõudma', 'jõudnud', 'jõudnud', 'jõudnud'], ['rahvusvaheline'], ['lugejaskond'], ['.'], ['seni'], ['vaid'], ['soome'], ['keel'], ['tõlkima', 'tõlgitud', 'tõlgitud', 'tõlgitud'], ['teos'], ['ilmuma'], ['äsja'], ['ka'], ['itaalia'], ['keel'], ['ning'], ['see'], ['esitlema'], ['Rooma'], ['reisikirjandus'], ['festival'], ['.'], ['tundma', 'tuntud', 'tuntud', 'tuntud'], ['reisikrijandus'], ['festival'], ['valima'], ['tänavu'], ['peakülaline'], ['Eesti'], [','], ['Ultima'], ['Thule'], ['ning'], ['Iidse-Põhjala', 'Iidse-Põhjala'], ['ja'], ['Vahemeri'], ['endisaegne'], ['kultuurikontakt'], ['j'], ['uks'], ['seetõttu'], [','], ['et'], ['eelmine'], ['nädal'], ['avaldama'], ['kirjastus'], ['Gangemi'], ['"'], ['hõbevalge'], ['"'], ['itaalia'], ['keel'], [','], ['vahendama'], ['"'], ['aktuaalne'], ['kaamera'], ['".']]
)



def test_text_setitem():
    text = words_sentences('''Lennart Meri "Hõbevalge" on jõudnud rahvusvahelise lugejaskonnani.''')
    l = Layer(name='test', attributes=['test1'])
    text['test'] = l

    assert text['test'] is l

    #assigning something that is not a layer
    with pytest.raises(AssertionError):
        text['test'] = '123'

    #getting something that is not in the dict
    with pytest.raises(KeyError):
        text['nothing']



def test_rewrite_access():
    import regex as re
    text = words_sentences('''
    Lennart Meri "Hõbevalge" on jõudnud rahvusvahelise lugejaskonnani.
    Seni vaid soome keelde tõlgitud teos ilmus äsja ka itaalia keeles
    ning seda esitleti Rooma reisikirjanduse festivalil.
    Tuntud reisikrijanduse festival valis tänavu peakülaliseks Eesti,
    Ultima Thule ning Iidse-Põhjala ja Vahemere endisaegsed kultuurikontaktid j
    ust seetõttu, et eelmisel nädalal avaldas kirjastus Gangemi "Hõbevalge"
    itaalia keeles, vahendas "Aktuaalne kaamera".''')
    rules = [
        ["…$", "Ell"],
        ["\.\.\.$", "Ell"],
        ["\.\.$", "Els"],
        ["\.$", "Fst"],
        [",$", "Com"],
        [":$", "Col"],
        [";$", "Scl"],
        ["(\?+)$", "Int"],
        ["(\!+)$", "Exc"],
        ["(---?)$", "Dsd"],
        ["(-)$", "Dsh"],
        ["\($", "Opr"],
        ["\)$", "Cpr"],
        ['\\\\"$', "Quo"],
        ["«$", "Oqu"],
        ["»$", "Cqu"],
        ["“$", "Oqu"],
        ["”$", "Cqu"],
        ["<$", "Grt"],
        [">$", "Sml"],
        ["\[$", "Osq"],
        ["\]$", "Csq"],
        ["/$", "Sla"],
        ["\+$", "crd"],
        ["L", "SUURL"]

    ]

    triggers = []
    targets = []
    for a, b in rules:
        triggers.append(
            {'lemma': lambda x, a=a: re.search(a, x)}
        )
        targets.append({'main': b}
                       )
    rules = list(zip(triggers, targets))

    class SENTINEL:
        pass

    def apply(trigger, dct):
        res = {}
        for k, func in trigger.items():
            match = dct.get(k, SENTINEL)
            if match is SENTINEL:
                return None  # dict was missing a component of trigger

            new = func(match)
            if not new:
                return None  # no match
            else:
                res[k] = new
        return res


    class Ruleset:
        def __init__(self, rules):
            self.rules = rules

        def rewrite(self, dct):
            ress = []
            for trigger, target in self.rules:
                context = apply(trigger, dct)
                if context is not None:
                    ress.append(self.match(
                        target, context
                    ))
            return ress

        def match(self, target, context):
            return target

    ruleset = Ruleset(rules)

    com_type = Layer(
        name='com_type',
        parent='morf_analysis',
        attributes=['main'],
        ambiguous=True
    )

    text._add_layer(com_type)

    def rewrite(source_layer, target_layer, rules):
        assert target_layer.layer.parent == source_layer.layer.name

        target_layer_name = target_layer.layer.name

        attributes = source_layer.layer.attributes
        for span in source_layer:
            dct = {}
            for k in attributes:
                dct[k] = getattr(span, k, None)[0]  # TODO: fix for nonambiguous layer!
            res = rules.rewrite(dct)

            for result in res:

                # TODO! remove indexing for nonambiguous layer
                newspan = span[0].__getattribute__('mark')(target_layer_name)
                for k, v in result.items():
                    setattr(newspan, k, v)

    rewrite(text.morf_analysis, text.com_type, ruleset)

    ##TODO
    # for i in text.words:
    #     if i.main:
    #         print(i.main)
    #         print(i.com_type)
    #         print(i.com_type.main)
    #         assert i.main == i.com_type.main
    #

    for i in text.com_type:
        print(i, i.morf_analysis)
    ## TODO
    # for i in text.com_type:
    #     print(i, i.lemma)