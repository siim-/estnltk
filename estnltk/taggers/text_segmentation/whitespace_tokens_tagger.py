#
#  WhiteSpaceTokensTagger splits text into tokens based on 
#  whitespaces (and whitespaces only).
#  Use this tagger if you have a text that has been already 
#  correctly split into tokens by whitespaces, and you do 
#  not need to apply any extra tokenization rules.
#  ( e.g. if you need to load/restore original tokenization 
#         of some pretokenized corpus )
#

from typing import MutableMapping, Sequence
import re

from estnltk.text import Layer
from estnltk.taggers import Tagger
from nltk.tokenize.regexp import WhitespaceTokenizer

tokenizer = WhitespaceTokenizer()

class WhiteSpaceTokensTagger(Tagger):
    """Splits text into tokens by whitespaces. 
       Use this tagger only if you have a text that has been already 
       correctly tokenized by whitespaces, and you do not need to apply 
       any extra tokenization rules. """
    output_layer = 'tokens'
    attributes   = ()
    conf_param   = ['depends_on', 'layer_name',  # <- For backward compatibility ...
                   ]


    def __init__(self, output_layer:str='tokens'):
        """
        Initializes WhiteSpaceTokensTagger.
        
        Parameters
        ----------
        output_layer: str (default: 'tokens')
            Name of the layer where tokenization results will
            be stored;
        """
        self.output_layer = output_layer
        self.input_layers = []
        self.layer_name   = self.output_layer  # <- For backward compatibility
        self.depends_on   = []                 # <- For backward compatibility


    def _make_layer(self, raw_text: str, layers: MutableMapping[str, Layer], status: dict) -> Layer:
        """Segments given Text into tokens. 
           Returns tokens layer.
        
           Parameters
           ----------
           raw_text: str
              Text string corresponding to the text which will be 
              tokenized;
              
           layers: MutableMapping[str, Layer]
              Layers of the raw_text. Contains mappings from the name 
              of the layer to the Layer object.
              
           status: dict
              This can be used to store metadata on layer tagging.
        """
        spans = list(tokenizer.span_tokenize(raw_text))
        return Layer(name=self.output_layer).from_records([{
                                                   'start': start,
                                                   'end': end
                                                  } for start, end in spans],
                                                 rewriting=True)

