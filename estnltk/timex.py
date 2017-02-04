# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

from .javaprocess import JavaProcess, JAVARES_PATH
from .names import *

from pprint import pprint

import os, os.path
import json, re
import datetime


# A hack for defining a string type common in Py 2 and Py 3
try:
    # Check whether basestring is supported (should be in Py 2.7)
    basestring
except NameError as e:
    # If not supported (in Py 3.x), redefine it as str
    basestring = str


class TimexTagger(JavaProcess):
    """ Wrapper class around Java-based temporal expression tagger (Ajavt).
        Processes whole texts and extracts & normalises temporal expressions (TIMEXes);
        
        Usage examples:
        
         1) Using a custom rules file:
         
                from estnltk import Text
                from estnltk.timex import TimexTagger
                mytimextagger = TimexTagger( rules_file = ...path_to_rules_file... )
                text    = Text('Täna on ilus ilm', timex_tagger = mytimextagger )
                timexes = text.timexes
         
         2) Passing the document creation time as a datetime object:
         
                import datetime
                from estnltk import Text
                text = Text('Täna on ilus ilm', creation_date=datetime.datetime(1986, 12, 21))
                timexes = text.timexes
              
         3) Passing the document creation time as a string:
         
            *) A fully specified creation date: 
              
                from estnltk import Text
                text = Text('Täna on ilus ilm', creation_date='1986-12-21')
                timexes = text.timexes
            
            *) An unknown/unspecified document creation date:
         
                from estnltk import Text
                text = Text('Eile oli ilus ilm', creation_date='XXXX-XX-XX')
                timexes = text.timexes
            
                  (affects normalisation: relative dates will also be unspecified)
            
    """
    
    def __init__(self, rules_file=None):
        use_rules_file = os.path.join(JAVARES_PATH, 'reeglid.xml') if not rules_file else rules_file
        if not os.path.exists( use_rules_file ):
            raise Exception('(!) Unable to find timex tagger rules file from the location:', use_rules_file )
        JavaProcess.__init__(self, 'Ajavt.jar', ['-pyvabamorf', '-r', use_rules_file])


    def _get_creation_date(self, **kwargs):
        ''' Gets a creation date from arguments or creates new if non given.
            Throws an exception in case of an unexpected creation date.
        '''
        creation_date_from_arg = kwargs.get('creation_date', None)
        if not creation_date_from_arg:
            # If document creation time is not given as an argument,
            # use the default creation time: execution time of the program
            creation_date = datetime.datetime.now()
            return creation_date.strftime('%Y-%m-%dT%H:%M')
        else:
            # Get creation date according to the type of argument:
            if isinstance(creation_date_from_arg, datetime.datetime):
                # Python's datetime object
                return creation_date_from_arg.strftime('%Y-%m-%dT%H:%M')
            elif isinstance( creation_date_from_arg, basestring ):
                # A string following ISO date&time format
                if re.match("[0-9X]{4}-[0-9X]{2}-[0-9X]{2}$", creation_date_from_arg):
                    return creation_date_from_arg + "TXX:XX"
                elif re.match("[0-9X]{4}-[0-9X]{2}-[0-9X]{2}T[0-9X]{2}:[0-9X]{2}$", creation_date_from_arg):
                    return creation_date_from_arg
        raise Exception('(!) Unexpected "creation_date" argument: ', creation_date_from_arg)


    def tag_document(self, document, **kwargs):
        # get the arguments
        remove_unnormalized_timexes = kwargs.get('remove_unnormalized_timexes', True)
        creation_date = self._get_creation_date( **kwargs )

        # add creation date to document
        document[CREATION_DATE] = creation_date

        # detect timexes
        input_data = {
            CREATION_DATE: creation_date,
            SENTENCES: [{WORDS: words} for words in document.divide()]
        }
        output = json.loads(self.process_line(json.dumps(input_data)))

        # process output
        timexes = collect_timexes(output)
        if remove_unnormalized_timexes:
            timexes = remove_unnormalized(timexes)

        text = document.text
        #  (!) Timexes need to be sorted in the order of their appearance in text;
        #  text splitting/dividing methods assume such order, and if this is not 
        #  provided, we may lose some timexes in the process of dividing ...
        sortedTidsAndTimexes = sorted( timexes.items(),key=lambda x:x[1][START] )
        document[TIMEXES] = [ convert_timex(timex, text) for tid, timex in sortedTidsAndTimexes ]
        return document


RENAMING_MAP = {
    'temporalFunction': TMX_TEMP_FUNCTION,
    'anchorTimeID': TMX_ANCHOR_TID,
    'beginPoint': TMX_BEGINPOINT,
    'endPoint': TMX_ENDPOINT,
}


def rename_attributes(timex):
    # rename javaStyle to python_style
    for oldKey, newKey in RENAMING_MAP.items():
        if oldKey in timex:
            timex[newKey] = timex[oldKey]
            del timex[oldKey]
    return timex


def collect_timexes(output):
    timexes = {}
    for sentidx, sentence in enumerate(output[SENTENCES]):
        for wordidx, word in enumerate(sentence[WORDS]):
            if TIMEXES in word:
                for timex in word[TIMEXES]:
                    timex = rename_attributes(timex)
                    timex[START] = word[START]
                    timex[END] = word[END]
                    # merge with existing reference to same timex, if it exists
                    tid = timex[TMX_TID]
                    if tid in timexes:
                        for k, v in timexes[tid].items():
                            if k == START:
                                timex[START] = min(v, timex[START])
                            elif k == END:
                                timex[END] = max(v, timex[END])
                            else:
                                timex[k] = v
                    timexes[tid] = timex
    return timexes


def remove_unnormalized(timexes):
    return dict((tid, timex) for tid, timex in timexes.items() if TMX_TYPE in timex and TMX_VALUE in timex)


def convert_timex(timex, text):
    # if TEXT is not provided (the case of empty TIMEX3 tag), also 
    # make the length of TIMEX zero
    if TEXT not in timex:
        # make start and end equal
        timex[START] = timex[END]
    if TMX_TEMP_FUNCTION in timex:
        tmp = timex[TMX_TEMP_FUNCTION].upper()
        if tmp.startswith('T'):
            timex[TMX_TEMP_FUNCTION] = True
        else:
            timex[TMX_TEMP_FUNCTION] = False
    # extract integer versions of timexes
    if TMX_TID in timex:
        tid = timex[TMX_TID]
        if tid.startswith('t'):
            tid = tid[1:]
        timex[TMX_ID] = int(tid)-1
    # extract anchor ids
    if TMX_ANCHOR_TID in timex:
        aid = timex[TMX_ANCHOR_TID]
        if aid != 't0' and '?' not in aid:  # refers to document creation date:
            timex[TMX_ANCHOR_ID] = int(aid[1:])-1
    return timex
