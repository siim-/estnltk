from collections import defaultdict

from estnltk import Text

from estnltk.taggers.morph_analysis.morf import VabamorfAnalyzer
from estnltk.taggers.morph_analysis.cb_disambiguator import CorpusBasedMorphDisambiguator

# ----------------------------------
#   Helper functions
# ----------------------------------

def collect_ambiguities( docs ):
    # Collect and index all morphological ambiguities from 
    # the given document collection
    ambiguities = dict()
    for doc_id, doc in enumerate(docs):
        for wid, word in enumerate(doc['words']):
            analyses = [(a.root, a.partofspeech, a.form) for a in word.morph_analysis]
            ambiguities[(doc_id,wid)] = analyses
    return ambiguities

def find_ambiguities_diff( ambiguities_a, ambiguities_b ):
    removed_ambiguities = defaultdict(list)
    added_ambiguities   = defaultdict(list)
    # Finds a difference between ambiguities_a and ambiguities_b
    for key_a in ambiguities_a.keys():
        if key_a in ambiguities_b:
            # Check if any ambiguities were removed
            for analysis_a in ambiguities_a[key_a]:
                if analysis_a not in ambiguities_b[key_a]:
                    removed_ambiguities[key_a].append( analysis_a )
            # Check if any ambiguities were introduced
            for analysis_b in ambiguities_b[key_a]:
                if analysis_b not in ambiguities_a[key_a]:
                    added_ambiguities[key_a].append( analysis_b )
        else:
            # All analyses from a have been removed
            removed_ambiguities[key_a] = ambiguities_a[key_a]
    for key_b in ambiguities_b.keys():
        if key_b not in ambiguities_a:
            # All analyses from a have been newly added 
            added_ambiguities[key_b] = ambiguities_b[key_b]
    return removed_ambiguities, added_ambiguities

morf_analyzer = VabamorfAnalyzer()

# ----------------------------------

def test_proper_names_disambiguation():
    # Case 1
    docs = [ Text('Perekonnanimi oli Nõmm.'), \
             Text('Kuidas seda hääldada: Nõmmil või Nõmmel?') ]
    for doc in docs:
        doc.tag_layer(['compound_tokens', 'words', 'sentences'])
        morf_analyzer.tag(doc)
    ambiguities_a = collect_ambiguities( docs )
    # Use corpus-based disambiguation:
    cb_disambiguator = CorpusBasedMorphDisambiguator()
    cb_disambiguator._test_predisambiguation(docs)
    # Find difference in ambiguities
    ambiguities_b = collect_ambiguities( docs )
    removed, added = find_ambiguities_diff( ambiguities_a, ambiguities_b )
    assert sorted(list(removed.items())) == [ ( (0, 0),[('Perekonna_nimi', 'H', 'sg n'),
                                                        ('Perekonnanim', 'H', 'adt'),
                                                        ('Perekonnanim', 'H', 'sg g'),
                                                        ('Perekonnanim', 'H', 'sg p'),
                                                        ('Perekonnanimi', 'H', 'sg g'),
                                                        ('Perekonnanimi', 'H', 'sg n')]),
                                              ( (0, 2), [('nõmm', 'S', 'sg n')]),
                                              ( (1, 4), [('Nõmmil', 'H', 'sg n'), ('Nõmmi', 'H', 'sg ad')]),
                                              ( (1, 6), [('nõmm', 'S', 'sg ad')]),
                                            ]
    assert list(added.items()) == []
    
    # Case 2
    docs = [ Text('Ott tahab võita ka Kuldgloobust.'), \
             Text('Kuidas see Otil õnnestub, ei tea. Aga Ott lubas pingutada.'), \
             Text('Võib-olla tuleks siiski teha Kuldgloobuse eesti variant.') ]
    for doc in docs:
        doc.tag_layer(['compound_tokens', 'words', 'sentences'])
        morf_analyzer.tag(doc)
    ambiguities_a = collect_ambiguities( docs )
    # Use corpus-based disambiguation:
    cb_disambiguator = CorpusBasedMorphDisambiguator()
    cb_disambiguator._test_predisambiguation(docs)
    # Find difference in ambiguities
    ambiguities_b = collect_ambiguities( docs )
    removed, added = find_ambiguities_diff( ambiguities_a, ambiguities_b )
    assert sorted(list(removed.items())) == [ ((0, 0), [('ott', 'S', 'sg n')]), \
                                              ((0, 4), [('kuld_gloobus', 'S', 'sg p')]),\
                                              ((1, 2), [('ott', 'S', 'sg ad')]), \
                                              ((1, 9), [('ott', 'S', 'sg n')]), \
                                              ((2, 4), [('kuld_gloobus', 'S', 'sg g')]), \
                                            ]
    assert list(added.items()) == []

