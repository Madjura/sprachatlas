"""Functions that help with the extraction of paragraphs and Noun Phrases from texts."""

__copyright__ = """
Copyright (C) 2017 Thomas Huber <huber150@stud.uni-passau.de, madjura@gmail.com>
Copyright (C) 2012 Vit Novacek (vit.novacek@deri.org), Digital Enterprise
Research Institute (DERI), National University of Ireland Galway (NUIG)
All rights reserved.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

// Modifications made to the original code by Vit Novacek
----------------
2017, Thomas Huber
- get_cooc: 
    * renamed to get_cooccurence
    * modified check of whether or not a string is purely non-alphanumeric to be more readable and effective
- text2cooc: 
    * renamed to extract_from_sentences
    * added noun phrase grammar to function instead of being global
- gen_src:
    * renamed to calculate_weighted_distance
    * updated to use Closeness objects to represent weighted distance
* comment and variable naming cleanup
"""
import math
from _collections import OrderedDict, defaultdict
from itertools import combinations

import nltk
from nltk.chunk.regexp import RegexpParser
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tree import Tree

from text.closeness import Closeness
from text.sentence import Sentence


def split_paragraphs(text):
    """
    Takes a text and collects the paragraphs of the text.

    :param text: The content of a text file.
    :return: A list of strings, where each element is a paragraph of the input text.
    """
    lines = text.split("\n")
    current_paragraph = []
    paragraphs = []
    # iterate over each line of the text, with .strip() applied to remove trailing whitespace
    for line in map(lambda x: x.strip(), lines):
        if len(line) > 0:
            # the line is NOT a paragraph if there is something there
            current_paragraph.append(line)
        elif current_paragraph:
            # line IS a paragraph
            paragraphs.append(" ".join(current_paragraph))
            current_paragraph.clear()
    # get the final paragraph
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))
    return paragraphs


def convert_pos_to_universal(source, tag):
    return {
        "stts": {
            "$(": "PUNCT",
            "$": "PUNCT",
            "$.": "PUNCT",
            "$,": "PUNCT",
            "ADJA": "ADJ",
            "ADJD": "ADJ",
            "ADV": "ADV",
            "APPO": "ADP",
            "APPR": "ADP",
            "APPRART": "ADP",
            "APZR": "ADP",
            "ART": "DET",
            "CARD": "NUM",
            "FM": "X",
            "ITJ": "INTJ",
            "KOKOM": "CCONJ",
            "KON": "CCONJ",
            "KOUI": "SCONJ",
            "KOUS": "SCONJ",
            "NE": "PROPN",
            "NN": "NOUN",
            "PAV": "ADV",
            "PDAT": "DET",
            "PDS": "PRON",
            "PIAT": "DET",
            "PIDAT": "DET",
            "PIS": "PRON",
            "PPER": "PRON",
            "PPOSAT": "DET",
            "PPOSS": "PRON",
            "PRELAT": "DET",
            "PROAV": "ADV",
            "PRELS": "PRON",
            "PRF": "PRON",
            "PTKA": "PART",
            "PTKANT": "PART",
            "PTKNEG": "PART",
            "PTKVZ": "ADP",
            "PTKZU": "PART",
            "PWAT": "DET",
            "PWAV": "ADV",
            "PWS": "PRON",
            "TRUNC": "X",
            "VAFIN": "AUX",
            "VAIMP": "AUX",
            "VAINF": "AUX",
            "VAPP": "AUX",
            "VMFIN": "VERB",
            "VMINF": "VERB",
            "VMPP": "VERB",
            "VVFIN": "VERB",
            "VVIMP": "VERB",
            "VVINF": "VERB",
            "VVIZU": "VERB",
            "VVPP": "VERB",
            "XY": "X",
            "": "X",
            "_SP": "X"
        },
        "penn-treebank": {
            "#": "SYM",
            "$": "SYM",
            '""': "PUNCT",
            ",": "PUNCT",
            "-LRB-": "PUNCT",
            "-RRB-": "PUNCT",
            ".": "PUNCT",
            ":": "PUNCT",
            "AFX": "ADJ",
            "CC": "CCONJ",
            "CD": "NUM",
            "DT": "DET",
            "EX": "PRON",
            "FW": "X",
            "HYPH": "PUNCT",
            "IN": "ADP",
            "JJ": "ADJ",
            "JJR": "ADJ",
            "JJS": "ADJ",
            "LS": "X",
            "MD": "VER",
            "NIL": "X",
            "NN": "NOUN",
            "NNP": "PROPN",
            "NNPS": "PROPN",
            "NNS": "NOUN",
            "PDT": "DET",
            "POS": "PART",
            "PRP": "PRON",
            "PRP$": "DET",
            "RB": "ADV",
            "RBR": "ADV",
            "RBS": "ADV",
            "RP": "ADP",
            "SYM": "SYM",
            "TO": "PART",
            "UH": "INTJ",
            "VB": "VERB",
            "VBD": "VERB",
            "VBG": "VERB",
            "VBN": "VERB",
            "VBP": "VERB",
            "VBZ": "VERB",
            "WDT": "DET",
            "WP": "PRON",
            "WP$": "DET",
            "WRB": "ADV",
            "``": "PUNCT",
            "''": "PUNCT",
            "": "X",
            "_SP": "X"
        }
    }[source][tag]


def get_cooccurence_spacy(chunk_trees, ignore_stopwords=True, language="english"):
    """
    Parses a chunk tree and gets co-occurance of terms.

    :param chunk_trees: Tree from the NLTK RegexParser, generated over POS-tagged sentences using the provided grammar.
    :param ignore_stopwords: Optional. Default: True. Whether stopwords are to be ignored or not.
    :param language: Optional. Default: English. The language of the texts over which the chunk trees were generated.
    :return: A list of co-occuring tokens and a simple parse tree generated over the leaves of  the chunks of the
        provided one.
    """
    triples = []
    simple_trees = []
    NP_GRAMMAR_SIMPLE = "NP: {<ADJ>*((<NOUN>|<PROPN>)|<ADJ>)+}"
    parser_simple = RegexpParser(NP_GRAMMAR_SIMPLE)
    for t in chunk_trees:
        entities = []
        for chunk in t:
            if isinstance(chunk, Tree) and chunk.label() == 'NP':
                # getting a tree for later processing of triples from the simple noun
                # phrases (if present)
                simple_trees.append(parser_simple.parse(chunk.leaves()))
                words = [word for word, _tag in chunk if (not (ignore_stopwords and word in stopwords.words(language)) or any([char.isalnum() for char in word]))]
                if len(words) > 0:
                    entities.append("_".join(words))
        for e1, e2 in combinations(entities, 2):
            triples.append((e1, "close to", e2))
            triples.append((e2, "close to", e1))
    return triples, simple_trees


def extract_from_sentences_spacy(sentences, is_stop, add_verbs=True, language="english"):
    pos_dictionary = {}
    NP_GRAMMAR_COMPOUND = "NP: {<ADJ>*((<NOUN>|<PROPN>)|<ADJ>)+((<ADP>|<PART>)?<ADJ>*((<NOUN>|<PROPN>)|<ADJ>)+)*((<CCONJ>|PUNCT)<ADJ>*((<NOUN>|<PROPN>)|<ADJ>)+((<ADP>|<PART>)?<ADJ>*((<NOUN>|<PROPN>)|<ADJ>)+)*)*}"
    for sentence in sentences:
        pos_dictionary[sentence.sentence_id] = [(token, tag) for token, tag in sentence.tokens.items()]
    parser_cmp = RegexpParser(NP_GRAMMAR_COMPOUND)
    term2sentence_id = defaultdict(lambda: set())
    for sentence_id, pos_tagged_tokens in pos_dictionary.items():
        if add_verbs:
            # updating the inverse occurrence index with verbs
            for subject, tag in pos_tagged_tokens:
                # check if subject is tagged as a verb
                if tag == "VERB" and not is_stop[sentence_id][subject]:
                    term2sentence_id[subject].add(sentence_id)
        # trying to parse the sentence_id into a top-level chunk tree
        tree = parser_cmp.parse(pos_tagged_tokens)
        # getting the top-level tree triples and decomposing the NPs
        cmp_triples, simple_trees = get_cooccurence_spacy([tree], ignore_stopwords=False, language=language)
        smp_triples, _ = get_cooccurence_spacy(simple_trees, ignore_stopwords=True, language=language)
        # updating the inverse occurrence index with NPs
        for subject, _, objecT in cmp_triples + smp_triples:
            if subject.lower() not in term2sentence_id:
                term2sentence_id[subject.lower()] = set()
            if objecT.lower() not in term2sentence_id:
                term2sentence_id[objecT.lower()] = set()
            term2sentence_id[subject.lower()].add(sentence_id)
            term2sentence_id[objecT.lower()].add(sentence_id)
    return term2sentence_id


def pos_tag_spacy(text, source):
    sentences = []
    is_stop = defaultdict(lambda: defaultdict(lambda: bool))
    for i, sentence in enumerate(list(text.sents)):
        tokens = OrderedDict()
        for token in sentence:
            # print(source, token.tag_, token, token.lemma_)
            tokens[token.lemma_] = convert_pos_to_universal(source, token.tag_)
            is_stop[i][token.lemma_] = token.is_stop
        sentences.append(Sentence(i, tokens))
    return sentences, is_stop


def pos_tag(text, tagger=None):
    """
    Tokenize a given text and generates a list of Sentence objects.

    :param text: Tokenizes a given text and generates a list of Sentence objects, with the appropiate POS-tags added.
    :param tagger: Optional. Default: None. Used to tag for languages other than English but must be provided.
    :return: A list of Sentence objects representing the sentences in the text.
    """
    sentences = []
    if tagger:
        sentences_tokenized = nltk.sent_tokenize(text)
        sentences_word_tokenized = [nltk.sent_tokenize(x) for x in sentences_tokenized]
        tagged_sentences = tagger.tag_sents(sentences_word_tokenized)
        for count, sentence in enumerate(tagged_sentences):
            tokens = OrderedDict()
            for word, tag in sentence:
                tokens[word] = tag
            sentences.append(Sentence(count, tokens))
        return sentences
    else:
        tagged_sentences = nltk.sent_tokenize(text)
        for count, sentence in enumerate(tagged_sentences):
            tokens = OrderedDict()
            # get the tokens and POS tags
            for word, tag in nltk.pos_tag(nltk.word_tokenize(sentence)):
                tokens[word] = tag
                # sentence is now tokenized and tokens have POS tags
            sentences.append(Sentence(count, tokens))
        return sentences


def extract_from_sentences(sentences, add_verbs=True, language="english"):
    """
    Processes Sentence objects to calculate contained Noun Phrases based on a given grammar and maps them to the
    sentences they occur in.

    :param sentences: A list of Sentence objects.
    :param add_verbs: Optional. Default: True. Whether or not verbs are to be added to the mapping.
    :param language: Optional. Default: English. The langue of the sentences.
    :return: A dictionary mapping tokens to the sentence IDs of the sentences they appear in.
    """
    # produce the mapping of sentences to their contained (words, pos) tuples
    pos_dictionary = {}
    NP_GRAMMAR_COMPOUND = "NP: {<JJ.*>*(<N.*>|<JJ.*>)+((<IN>|<TO>)?<JJ.*>*(<N.*>|<JJ.*>)+)*((<CC>|,)<JJ.*>*(<N.*>|<JJ.*>)+((<IN>|<TO>)?<JJ.*>*(<N.*>|<JJ.*>)+)*)*}"
    for sentence in sentences:
        pos_dictionary[sentence.sentence_id] = [(token, tag) for token, tag in sentence.tokens.items()]
    parser_cmp = RegexpParser(NP_GRAMMAR_COMPOUND)
    term2sentence_id = {}
    lemmatizer = WordNetLemmatizer()
    for sentence_id, pos_tagged_tokens in pos_dictionary.items():
        if add_verbs:
            # updating the inverse occurrence index with verbs
            for subject, tag in pos_tagged_tokens:
                # check if subject is tagged as a verb
                if tag.startswith("VB"):
                    verb = lemmatizer.lemmatize(subject, "v").lower()
                    if verb not in stopwords.words(language):
                        if verb not in term2sentence_id:
                            term2sentence_id[verb] = set()
                        term2sentence_id[verb].add(sentence_id)
        # trying to parse the sentence_id into a top-level chunk tree
        tree = parser_cmp.parse(pos_dictionary[sentence_id])
        # getting the top-level tree triples and decomposing the NPs
        cmp_triples, simple_trees = get_cooccurence([tree], ignore_stopwords=False, language=language)
        smp_triples, _ = get_cooccurence(simple_trees, ignore_stopwords=True, language=language)
        # updating the inverse occurrence index with NPs 
        for subject, _, objecT in cmp_triples + smp_triples:
            if subject.lower() not in term2sentence_id:
                term2sentence_id[subject.lower()] = set()
            if objecT.lower() not in term2sentence_id:
                term2sentence_id[objecT.lower()] = set()
            term2sentence_id[subject.lower()].add(sentence_id)
            term2sentence_id[objecT.lower()].add(sentence_id)
    return term2sentence_id


def extract_from_sentence_theutonista(sentences):
    pass



def get_cooccurence(chunk_trees, ignore_stopwords=True, language="english"):
    """
    Parses a chunk tree and gets co-occurance of terms.

    :param chunk_trees: Tree from the NLTK RegexParser, generated over POS-tagged sentences using the provided grammar.
    :param ignore_stopwords: Optional. Default: True. Whether stopwords are to be ignored or not.
    :param language: Optional. Default: English. The language of the texts over which the chunk trees were generated.
    :return: A list of co-occuring tokens and a simple parse tree generated over the leaves of  the chunks of the
        provided one.
    """
    triples = []
    simple_trees = []
    lemmatizer = WordNetLemmatizer()
    NP_GRAMMAR_SIMPLE = "NP: {<JJ.*>*(<N.*>|<JJ.*>)+}"
    parser_simple = RegexpParser(NP_GRAMMAR_SIMPLE)
    for t in chunk_trees:
        entities = []
        for chunk in t:
            if isinstance(chunk, Tree) and chunk.label() == 'NP':
                # getting a tree for later processing of triples from the simple noun 
                # phrases (if present)
                simple_trees.append(parser_simple.parse(chunk.leaves()))
                words = []
                for word, tag in chunk:
                    if (ignore_stopwords and word in stopwords.words(language)) or \
                            (not any(char.isalnum() for char in word)):
                        # do not process stopwords for simple trees, do not process purely 
                        # non alphanumeric characters
                        continue
                    if tag.startswith('N'):
                        words.append(lemmatizer.lemmatize(word, 'n'))
                    elif tag.startswith('J'):
                        words.append(lemmatizer.lemmatize(word, 'a'))
                    else:
                        words.append(word)
                if len(words) > 0:
                    entities.append("_".join(words))
        for e1, e2 in combinations(entities, 2):
            triples.append((e1, "close to", e2))
            triples.append((e2, "close to", e1))
    return triples, simple_trees


def calculate_weighted_distance(token2sentences, *, paragraph_id=str, distance_threshold=5, weight_threshold=1/3):
    """
    Calculates the weighted distance between tokens given an inverse index mapping the tokens to the sentences they
    appear in. The distance is calculated by summing up 1/(1+distance) for each combination of positions of two tokens.

    :param token2sentences: The inverse index mapping tokens to the sentences they appear in.
    :param paragraph_id: The ID of the paragraph currently being processed, the one the sentences belong to.
    :param distance_threshold: Optional. Default: 5. The maximum distance in sentences that token can be apart to still
            be considered.
    :param weight_threshold: Optional. Default: 1/3. The minimum weight two tokens need to have to be considered.
    :return: A list of Closeness objects, representing the weighted distance between pairs of tokens.
    """
    closeness_list = []
    # get all term combinations to see if they are close to each other
    for term1, term2 in combinations(list(token2sentences.keys()), 2):
        w = 0.0
        # get positions of first term
        # positions are always per paragraph
        for position1 in token2sentences[term1]:
            # get positions of second term
            for position2 in token2sentences[term2]:
                # get the distance between the terms, measured in "terms between"
                distance = math.fabs(position1 - position2)
                # check if terms are close enough to each other
                if distance < distance_threshold:
                    # calculate new weight
                    w += 1 / (1 + distance)
        # check if terms are relevant enough
        if w > weight_threshold:
            closeness_list.append(Closeness(term1, term2, w, paragraph_id))
    w2statements = defaultdict(list)
    for closeness in closeness_list:
        w2statements[closeness.closeness].append(closeness)
    # get weight values in descending orders - why?
    keys = list(w2statements.keys())
    keys.sort(reverse=True)
    closenesses = []
    # get list of closeness, ordered by descending weight
    for key in keys:
        for closeness in w2statements[key]:
            closenesses.append(closeness)
    return closenesses


def calculate_weighted_distance_theutonista(sentence_id, character2pos, distance_lim=5, weight_lim=1/3):
    pass