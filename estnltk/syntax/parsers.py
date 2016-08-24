# -*- coding: utf-8 -*- 
#
#   Estonian syntactic parsers under a unified interface;
#   
#   Aims to support:
#    *) VISL-CG3 based syntactic analysis (VISLCG3Parser);
#    *) MaltParser based syntactic analysis (MaltParser);
#

import os.path

from estnltk.names import *

from estnltk.maltparser_support import MALTPARSER_PATH, MALTPARSER_MODEL, MALTPARSER_JAR
from estnltk.maltparser_support import convertTextToCONLLstr, _executeMaltparser, augmentTextWithCONLLstr
from estnltk.maltparser_support import align_CONLL_with_Text

from syntax_preprocessing import SyntaxPreprocessing
from vislcg3_syntax import VISLCG3Pipeline, cleanup_lines, align_cg3_with_Text

from utils import normalise_alignments, build_trees_from_text

# Used constants
CONLL_DATA    = 'conll'
VISLCG3_DATA  = 'vislcg3'
LAYER_CONLL   = 'conll_syntax'
LAYER_VISLCG3 = 'vislcg3_syntax'

SENT_ID         = 'sent_id'
PARSER_OUT      = 'parser_out'
INIT_PARSER_OUT = 'init_parser_out'

# ==================================================================================
# ==================================================================================
#   VISL-CG3 based syntactic analyser
# ==================================================================================
# ==================================================================================

class VISLCG3Parser(object):
    ''' A wrapper for Estonian VISLCG3 based syntactic parsing pipeline. 
    
        Unifies processing done in SyntaxPreprocessing() and VISLCG3Pipeline(), and 
        post-processing done in  align_cg3_with_Text() and normalise_alignments() 
        into a common analysis pipeline, which produces a syntactic analyses for
        a Text object.
        
        Example usage:
            #
            # vislcg_cmd - provide full path to vislcg3 executable 
            #              ('vislcg3' or 'vislcg3.exe')
            # text       - EstNLTK Text object to be analysed;
            #
            parser = VISLCG3Parser( vislcg_cmd=vislcg_cmd )
            
            # parse text, and return results as list of lines from vislcg3's output
            results1 = parser.parse_text( text, return_type = "vislcg3" )
            for line in results1:
                print(line)
            
            # results are also packed in Text object, on the layer named LAYER_VISLCG3:
            for word_id_in_text, syntax_analysis in enumerate( text[LAYER_VISLCG3] ):
                parser_out = syntax_analysis[PARSER_OUT]
                print(word_id_in_text, parser_out)
            

    '''
    
    preprocessor      = None 
    vislcg3_processor = None
    
    def __init__( self, **kwargs):
       '''  Initializes VISLCG3 based syntactic analyzer's wrapper.
        
            Parameters
            -----------
            preprocessor : SyntaxPreprocessing
                A custom syntax pre-processing pipeline to be used in the parser.
                If omitted (default), the default constructor is used to create a new 
                SyntaxPreprocessing() object, and the created object is assigned to 
                preprocessor.
                
            vislcg3_processor : VISLCG3Pipeline
                A custom vislcg3 processing pipeline to be used in the parser.
                If omitted (default), a new VISLCG3Pipeline() object is created and 
                assigned to vislcg3_processor.               
            
            fs_to_synt_rules : str
                Name of the file containing rules for mapping from Filosoft's old mrf 
                format to syntactic analyzer's preprocessing mrf format;
                This argument is used in initiating SyntaxPreprocessing (preprocessor).
                (Defaults to: 'tmorftrtabel.txt' in 'syntax/files')
                
            subcat_rules : str
                Name of the file containing rules for adding subcategorization information
                to verbs/adpositions;
                This argument is used in initiating SyntaxPreprocessing (preprocessor).
                (Defaults to: 'abileksikon06utf.lx' in 'syntax/files')
                
            vislcg_cmd : str
                Name of visl_cg3 binary executable. If the executable is accessible from 
                system's PATH variable, full path can be omitted, otherwise, the name must 
                contain full path to the executable.
                This argument is used in initiating VISLCG3Pipeline (vislcg3_processor).
                Default: 'vislcg3'
            
            pipeline : list of str
                List of VISLCG3 rule file names. In the processing phase, these rules
                are executed exactly the same order as in the list.
                NB! If the rule file is given without path, it is assumed that the file
                resides in the directory *rules_dir*; Otherwise, a full path to the rule
                file must be provided within the name;
                This argument is used in initiating VISLCG3Pipeline (vislcg3_processor).
                
            rules_dir : str
                A default directory from where to find rules that are executed on the 
                pipeline.
                If a file name listed in *pipeline* does not contain path, it is assumed 
                to reside within *rules_dir*;
                This argument is used in initiating VISLCG3Pipeline (vislcg3_processor).
                Defaults to: 'syntax/files'

       '''
       # get custom pipelines (if provided)
       for argName, argVal in kwargs.items():
            if argName.lower in ['preprocessor', 'preproc']:
                assert isinstance(argVal, SyntaxPreprocessing), \
                    '(!) "preprocessor" must be from SyntaxPreprocessing class.'
                self.preprocessor = argVal
            elif argName.lower in ['vislcg3_processor', 'vislcg3_proc']:
                assert isinstance(argVal, VISLCG3Pipeline), \
                    '(!) "vislcg3_processor" must be from VISLCG3Pipeline class.'
                self.vislcg3_processor = argVal
       # initialize pre-processing pipeline
       if not self.preprocessor:
            new_kwargs = self._filter_kwargs( \
                ['subcat_rules','fs_to_synt_rules','allow_to_remove'], **kwargs )
            self.preprocessor = SyntaxPreprocessing( **new_kwargs )
       # initialize vislcg3 pipeline
       if not self.vislcg3_processor:
            new_kwargs = self._filter_kwargs( \
                ['pipeline','rules_dir','vislcg_cmd','vislcg'], **kwargs )
            self.vislcg3_processor = VISLCG3Pipeline( **new_kwargs )
    
    
    def parse_text(self, text, **kwargs):
        """ Parses given text with VISLCG3 based syntactic analyzer. 
        
            As a result of parsing, the input Text object will obtain a new 
            layer named LAYER_VISLCG3,  which  contains  a  list  of  dicts.
            Each dicts corresponds to analysis of a single word token, and
            has the following attributes (at minimum):
              'start'      -- start index of the word in Text;
              'end'        -- end index of the word in Text;
              'sent_id'    -- index of the sentence in Text, starting from 0;
              'parser_out' -- list of analyses from the output of the 
                              syntactic parser;
                In the list of analyses, each item has the following structure:
                    [ syntactic_label, index_of_the_head ]
                *) syntactic_label:
                       surface syntactic label of the word, e.g. '@SUBJ', 
                       '@OBJ', '@ADVL';
                *) index_of_the_head:
                       index of the head (in the sentence); 
                       -1 if the current token is root;
            
            Parameters
            -----------
            text : estnltk.text.Text
               The input text that should be analysed for dependency relations;
               
            return_type : string
                If return_type=="text" (Default), 
                    returns the input Text object;
                If return_type=="vislcg3", 
                    returns VISLCG3's output: a list of strings, each element in 
                    the list corresponding to a line from VISLCG3's output;
                If return_type=="trees", 
                    returns all syntactic trees of the text as a list of 
                    EstNLTK's Tree objects (estnltk.syntax.utils.Tree);
                If return_type=="dep_graphs", 
                    returns all syntactic trees of the text as a list of NLTK's 
                    DependencyGraph objects 
                    (nltk.parse.dependencygraph.DependencyGraph);
                Regardless the return type, the layer containing dependency syntactic
                information ( LAYER_VISLCG3 ) will be attached to the text object;
            
            augment_words : bool
                Specifies whether words in the input Text are to be augmented with 
                the syntactic information (SYNTAX_LABEL, SYNTAX_HEAD and DEPREL);
                (!) This functionality is added to achieve a compatibility with the 
                old way syntactic processing, but it will be likely deprecated in 
                the future.
                Default: False
            
            Other arguments are the arguments that can be passed to methods:
               vislcg3_syntax.process_lines(), 
               vislcg3_syntax.align_cg3_with_Text(),
               normalise_alignments()
            
            keep_old : bool
                Optional argument specifying  whether the old analysis lines 
                should be preserved after overwriting 'parser_out' with new analysis 
                lines;
                If True, each dict will be augmented with key 'init_parser_out' 
                which contains the initial/old analysis lines;
                Default:False
            
        """
        # a) get the configuration:
        augment_words    = False
        all_return_types = ["text","vislcg3","trees","dep_graphs"]
        return_type      = all_return_types[0]
        for argName, argVal in kwargs.items():
            if argName.lower() == 'return_type':
                if argVal.lower() in all_return_types:
                    return_type = argVal.lower()
                else:
                    raise Exception(' Unexpected return type: ', argVal)
            elif argName.lower() == 'augment_words' and argVal in [True, False]:
                augment_words = argVal
        kwargs['split_result']  = True
        kwargs['clean_up']      = True
        kwargs['remove_clo']    = kwargs.get('remove_clo', True)
        kwargs['remove_cap']    = kwargs.get('remove_cap', True)
        kwargs['keep_old']      = kwargs.get('keep_old',  False)
        kwargs['double_quotes'] = 'unesc'
        
        # b) process:
        result_lines1 = \
            self.preprocessor.process_Text(text, **kwargs)
        result_lines2 = \
            self.vislcg3_processor.process_lines(result_lines1, **kwargs)
        alignments = \
            align_cg3_with_Text(result_lines2, text, **kwargs)
        alignments = \
            normalise_alignments( alignments, data_type=VISLCG3_DATA, **kwargs )
        
        # c) attach & return results
        text[LAYER_VISLCG3] = alignments
        if augment_words:
            self._augment_text_w_syntactic_info( text, text[LAYER_VISLCG3] )
        if return_type   == "vislcg3":
            return result_lines2
        elif return_type == "trees":
            return build_trees_from_text( text, layer=LAYER_VISLCG3, **kwargs )
        elif return_type == "dep_graphs":
            trees = build_trees_from_text( text, layer=LAYER_VISLCG3, **kwargs )
            graphs = [tree.as_dependencygraph() for tree in trees]
            return graphs
        else:
            return text
    
    
    def _filter_kwargs(self, keep_list, **kwargs):
        ''' Filters the dict of *kwargs*, keeping only arguments 
            whose keys are in *keep_list* and discarding all other
            arguments.
            
            Based on the filtring, constructs and returns a new 
            dict.
        '''
        new_kwargs = {}
        for argName, argVal in kwargs.items():
            if argName.lower() in keep_list:
                new_kwargs[argName.lower()] = argVal
        return new_kwargs


    def _augment_text_w_syntactic_info( self, text, text_layer ):
        ''' Augments given Text object with the syntactic information 
            from the *text_layer*. More specifically, adds information 
            about SYNTAX_LABEL, SYNTAX_HEAD and DEPREL to each token 
            in the Text object;
            
            (!) Note: this method is added to provide some initial
            consistency with MaltParser based syntactic parsing;
            If a better syntactic parsing interface is achieved in
            the future, this method will be deprecated ...
        '''
        j = 0
        for sentence in text.divide( layer=WORDS, by=SENTENCES ):
            for i in range(len(sentence)):
                estnltkToken = sentence[i]
                vislcg3Token = text_layer[j]
                parse_found = False
                if PARSER_OUT in vislcg3Token:
                    if len( vislcg3Token[PARSER_OUT] ) > 0:
                        firstParse = vislcg3Token[PARSER_OUT][0]
                        # Fetch information about the syntactic relation:
                        estnltkToken[SYNTAX_LABEL] = str(i)
                        estnltkToken[SYNTAX_HEAD]  = str(firstParse[1])
                        # Fetch the name of the surface syntactic relation
                        deprels = '|'.join( [p[0] for p in vislcg3Token[PARSER_OUT]] )
                        estnltkToken[DEPREL]       = deprels
                        parse_found = True
                if not parse_found:
                    raise Exception("(!) Unable to retrieve syntactic analysis for the ",\
                                    estnltkToken, ' from ', vislcg3Token )
                j += 1


# ==================================================================================
# ==================================================================================
#   MaltParser
# ==================================================================================
# ==================================================================================

class MaltParser:
    '''  A wrapper around Java-based MaltParser. Allows to process EstNLTK Text
        objects with Maltparser in order to obtain dependency syntactic relations
        between the words in the sentence.
        
        Example usage:
            #
            # text       - EstNLTK Text object to be analysed;
            #
            parser = MaltParser( vislcg_cmd=vislcg_cmd )
            
            # parse text, and return results as list of lines from maltparser's output
            results1 = parser.parse_text( text, return_type = "conll" )
            for line in results1:
                print(line)
            
            # results are also packed in Text object, on the layer named LAYER_CONLL:
            for word_id_in_text, syntax_analysis in enumerate( text[LAYER_CONLL] ):
                parser_out = syntax_analysis[PARSER_OUT]
                print(word_id_in_text, parser_out)
    '''

    maltparser_dir    = MALTPARSER_PATH
    model_name        = MALTPARSER_MODEL
    maltparser_jar    = MALTPARSER_JAR
    add_ambiguous_pos = True
    
    def __init__( self, **kwargs):
        ''' Initializes MaltParser's wrapper. 
        
            Parameters
            -----------
            maltparser_dir : str
                Directory that contains Maltparser jar file and model file;
                This directory is also used for storing temporary files, so 
                writing should be allowed in it;
                
            model_name : str
                Name of the Maltparser's model;
                
            maltparser_jar : str    
                Name of the Maltparser jar file (e.g. 'maltparser-1.8.jar');
                
            add_ambiguous_pos : boolean
                Whether ambiguous POS tags should be rewritten as a fine-grained 
                POS tags (see convertTextToCONLLstr() for details);
                NB! Requires that MaltParser has been trained with this setting;
        '''
        for argName, argVal in kwargs.items():
            if argName == 'maltparser_dir':
                self.maltparser_dir = argVal
            elif argName == 'model_name':
                self.model_name = argVal
            elif argName == 'maltparser_jar':
                self.maltparser_jar = argVal
            elif argName == 'add_ambiguous_pos':
                self.add_ambiguous_pos = bool(argVal)
            else:
                raise Exception(' Unsupported argument given: '+argName)
        if not self.maltparser_dir:
            raise Exception('Missing input argument: MaltParser directory')
        elif not os.path.exists(self.maltparser_dir):
            raise Exception('Invalid MaltParser directory:',self.maltparser_dir)
        elif not self.maltparser_jar:
            raise Exception('Missing input argument: MaltParser jar file name')
        elif not self.model_name:
            raise Exception('Missing input argument: MaltParser model name')


    def parse_text( self, text, **kwargs ):
        ''' Parses given text with Maltparser. 
        
            As a result of parsing, the input Text object will obtain a new 
            layer named LAYER_CONLL,  which  contains  a  list  of  dicts.
            Each dicts corresponds to analysis of a single word token, and
            has the following attributes (at minimum):
              'start'      -- start index of the word in Text;
              'end'        -- end index of the word in Text;
              'sent_id'    -- index of the sentence in Text, starting from 0;
              'parser_out' -- list of analyses from the output of the 
                              syntactic parser;
                In the list of analyses, each item has the following structure:
                    [ syntactic_label, index_of_the_head ]
                *) syntactic_label:
                       surface syntactic label of the word, e.g. '@SUBJ', 
                       '@OBJ', '@ADVL';
                *) index_of_the_head:
                       index of the head (in the sentence); 
                       -1 if the current token is root;
            
            Parameters
            -----------
            text : estnltk.text.Text
               The input text that should be analysed for dependency relations;
            
            return_type : string
                If return_type=="text" (Default), 
                    returns the input Text object;
                If return_type=="conll", 
                    returns Maltparser's results as list of CONLL format strings, 
                    each element in the list corresponding to one line in 
                    MaltParser's output;
                If return_type=="trees", 
                    returns all syntactic trees of the text as a list of 
                    EstNLTK's Tree objects (estnltk.syntax.utils.Tree);
                If return_type=="dep_graphs", 
                    returns all syntactic trees of the text as a list of NLTK's 
                    DependencyGraph objects 
                    (nltk.parse.dependencygraph.DependencyGraph);
                Regardless the return type, the layer containing dependency syntactic
                information ( LAYER_CONLL ) will be attached to the text object;
            
            augment_words : bool
                Specifies whether words in the input Text are to be augmented with 
                the syntactic information (SYNTAX_LABEL, SYNTAX_HEAD and DEPREL);
                (!) This functionality is added to achieve a compatibility with the 
                old way syntactic processing, but it will be likely deprecated in 
                the future.
                Default: False
            
            Other arguments are the arguments that can be passed to methods:
               maltparser_support.align_CONLL_with_Text(),
               normalise_alignments()
            
            keep_old : bool
                Optional argument specifying  whether the old analysis lines 
                should be preserved after overwriting 'parser_out' with new analysis 
                lines;
                If True, each dict will be augmented with key 'init_parser_out' 
                which contains the initial/old analysis lines;
                Default:False
        
        '''
        # a) get the configuration:
        augment_words    = False
        all_return_types = ["text", "conll", "trees", "dep_graphs"]
        return_type      = all_return_types[0]
        for argName, argVal in kwargs.items():
            if argName == 'return_type':
                if argVal.lower() in all_return_types:
                    return_type = argVal.lower()
                else:
                    raise Exception(' Unexpected return type: ', argVal)
            elif argName.lower() == 'augment_words':
                augment_words = bool(argVal)
        
        # b) process:
        #  If text has not been morphologically analysed yet, add the 
        #  morphological analysis
        if not text.is_tagged(ANALYSIS):
            text.tag_analysis()
        # Obtain CONLL formatted version of the text
        textConllStr = convertTextToCONLLstr(text, addDepLabels = False, \
                                                   addAmbiguousPos = self.add_ambiguous_pos)
        # Execute MaltParser and get results as CONLL formatted string
        resultsConllStr = \
            _executeMaltparser( textConllStr, self.maltparser_dir, \
                                              self.maltparser_jar, \
                                              self.model_name )
        # Align the results with the initial text
        alignments = \
            align_CONLL_with_Text( resultsConllStr, text, **kwargs )
        alignments = \
            normalise_alignments( alignments, data_type=CONLL_DATA, **kwargs )
        
        # c) attach & return results
        text[LAYER_CONLL] = alignments
        if augment_words:
            # Augment the input text with the dependency relation information 
            # obtained from MaltParser 
            # (!) Note: this will be deprecated in the future
            augmentTextWithCONLLstr( resultsConllStr, text )
        if return_type   == "conll":
            return resultsConllStr
        elif return_type == "trees":
            return build_trees_from_text( text, layer=LAYER_CONLL, **kwargs )
        elif return_type == "dep_graphs":
            trees = build_trees_from_text( text, layer=LAYER_CONLL, **kwargs )
            graphs = [tree.as_dependencygraph() for tree in trees]
            return graphs
            # An alternative:
            # Return DependencyGraphs
            #from nltk.parse.dependencygraph import DependencyGraph
            #all_trees = []
            #for tree_str in ("\n".join(resultsConllStr)).split('\n\n'):
            #    t = DependencyGraph(tree_str)
            #    all_trees.append(t)
            #return all_trees
        else:
            return text
