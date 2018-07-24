#!/usr/bin/env python3
"""
Allows the execution of extract_step.
In this step the texts are pre-processed, they are tokenized and POS-tags are assigned.
"""
import os
import pickle

import spacy
from django.db import transaction, IntegrityError
from nltk.tag.stanford import StanfordPOSTagger
from pycallgraph.output.graphviz import GraphvizOutput
from pycallgraph.pycallgraph import PyCallGraph

from extract.text_extract import split_paragraphs, pos_tag, extract_from_sentences, \
    calculate_weighted_distance, pos_tag_spacy, extract_from_sentences_spacy, extract_from_sentence_theutonista, \
    calculate_weighted_distance_theutonista
from sprachatlas import setup
from text.paragraph import Paragraph
from util import paths

setup()
from dragnapp import models as dragnmodels

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
"""

german = spacy.load("de_core_news_sm")
english = spacy.load("en_core_web_sm")


def make_folders(alias=None):
    """
    Creates the folders required for using the system.
    The path to the folders can be found in the "util" package.

    :param alias: The Alias of the texts.
    """
    for path in paths.ALL:
        if not alias:
            if not os.path.exists(path):
                os.makedirs(path, 0o755)
        else:
            # folder = os.path.join(path, alias)
            folder = path + "/" + alias
            if not os.path.exists(folder) and path not in paths.EXCLUDE:
                os.makedirs(folder, 0o755)


def extract_step_db(text_path=paths.TEXT_PATH, *, language="english", texts=None, distance_threshold=2,
                    weight_threshold=0.76):
    # if specified, use stanford pos for that language
    texts = os.listdir(text_path) if not texts else texts
    used_texts = []
    for text in texts:
        if not text.endswith(".txt"):
            # support different file types here
            continue
        textpath = os.path.join(paths.TEXT_PATH, text)
        text_instance, _ = dragnmodels.Text.objects.get_or_create(name=text, path=textpath)
        used_texts.append(text_instance)
        with open(textpath, "r", encoding="utf-8") as current_text:
            text_content = current_text.read()
            # split the text into paragraphs first
            paragraphs = split_paragraphs(text_content)
            # take each paragraph, pos tag each paragraph content
            paragraph_list = []
            text_instance.paragraphs = len(paragraphs)
            text_instance.save()
            print(f"Current text: {text}")
            # bar = progressbar.ProgressBar(max_value=len(paragraphs) - 1)
            closeness_instances = []
            with transaction.atomic():
                for count, paragraph in enumerate(paragraphs):
                    # bar.update(count)
                    # make new paragraph, with pos-tagged sentence list
                    if language == "english":
                        doc = english(text_content)
                        source = "penn-treebank"
                    elif language == "german":
                        doc = german(text_content)
                        source = "stts"
                    else:
                        raise Exception("No language selected")
                    pos, is_stop = pos_tag_spacy(doc, source)
                    new_paragraph = Paragraph(count, pos, text)
                    paragraph_list.append(new_paragraph)
                    text2sentence = extract_from_sentences_spacy(
                        new_paragraph.sentences, is_stop, add_verbs=True, language=language)
                    closeness_list = calculate_weighted_distance(
                        text2sentence, paragraph_id=f"{text}_{count}", distance_threshold=distance_threshold,
                        weight_threshold=weight_threshold)
                    # can be a problem if texts have the same name but different paragraph contents, TODO: fix this
                    paragraph_instance, _ = dragnmodels.Paragraph.objects.get_or_create(
                        text=text_instance, position=count, content=paragraph)
                    for c in closeness_list:
                        closeness_instances.append(dragnmodels.Closeness(
                            paragraph=paragraph_instance, token1=c.term, token2=c.close_to, closeness=c.closeness))

            try:
                with transaction.atomic():
                    for c in closeness_instances:
                        c.save()
            except IntegrityError as e:
                # assumed to have already been processed (all of them)
                print(f"Exception while saving Closeness:\n{e}")
    identifier = ",".join(sorted([x.name for x in used_texts]))
    alias, created = dragnmodels.Alias.objects.get_or_create(identifier=identifier)
    if created or not alias.texts.all():
        alias.texts.add(*used_texts)


def extract_step(text_path: str = paths.TEXT_PATH, language="english", texts: [str] = None, alias=None):
    """
    Processes all files in a given folder.
    The process is as follows:
        1) Read the content of the file
        2) Split the content into Paragraph objects (each Paragraph has a list
            of containing sentences)
        3) For each paragraph:
            3.1) POS-tag the sentences
            3.2) Map the tokens to the sentence-position in the paragraph
                Example:
                    Paragraph:
                        Paul threw the red ball. The ball landed on the roof.
                    Sentences:
                        [Paul threw the red ball., The ball landed on the roof.]
                    Tokens:
                        [Paul, threw, the, red, ball, landed, on, roof]
                    Mapping:
                        [Paul: (0), threw: (0), the: (0, 1), ...]
            3.3) Generate the "Closeness" for each combination of tokens
                The weighting of the "Closeness" is calculated like so:
                    - For each combination of tokens, check all combinations
                        of positions.
                    - Check the distance (math.abs()) of the distances
                    - If it is below the threshold (default 5), add
                        the following to the current weight:
                            1/(1 + distance)
                    - If it is above the threshold, continue with the next
                        position
                    - After all positional combinations are checked, create
                        a "Closeness" object for the two tokens, with the weight
                        being the value that was calculated as above IF the
                        weight is above the threshold (1/3). If it is not,
                        continue with the next token.

                        In the example above the weight would be 1.5, so a
                        new Closeness object would be created and added to the
                        list.
            3.4) Add the resulting list from 3.3) to a list and continue with
                the next paragraph
        4) Write the resulting list of "Closeness" objects for each text
            to the disk.
    :param text_path: The path to the folder where the files are.
    :param language: Optional. Default: "english". The language of the texts.
    :param texts: Optional. A list of strings of filenames to be processed. If not provided, all texts in the system
        will be used.
    :param alias: Optional. The Alias of the collection of texts.
    """
    tagger = None
    _path_to_jar = paths.STANFORD_POS_PATH
    # check if tagger for language is specified
    model = paths.TAGGER_TO_LANGUAGE[language]
    # if specified, use stanford pos for that language
    if model:
        tagger = StanfordPOSTagger(model, _path_to_jar)
    closeness = []
    files = os.listdir(text_path)
    if texts:
        files = texts
    for text in files:
        if not text.endswith(".txt"):
            # support different file types here
            continue
        with (open(paths.TEXT_PATH + "/" + text, "r", encoding="utf-8")) as current_text:
            text_content = current_text.read()
            # split the text into paragraphs first
            paragraphs = split_paragraphs(text_content)
            # take each paragraph, pos tag each paragraph content
            paragraph_list = []
            with open(paths.TEXT_META_PATH + "/{}_meta".format(text), "w", encoding="utf8") as metafile:
                metafile.write("PARAGRAPHS: {}".format(len(paragraphs)))
            print("Current text: {}".format(text))
            # bar = progressbar.ProgressBar(max_value=len(paragraphs) - 1)
            for count, paragraph in enumerate(paragraphs):
                # bar.update(count)
                # make new paragraph, with pos-tagged sentence list
                pos = pos_tag(paragraph, tagger)
                new_paragraph = Paragraph(count, pos, text)
                paragraph_list.append(new_paragraph)
                # {'study': {0}, 'temperament': {0}}
                text2sentence = extract_from_sentences(new_paragraph.sentences, language)
                # terms = text2sentence.keys()
                closeness_list = calculate_weighted_distance(text2sentence,
                                                             paragraph_id="{}_{}".format(str(text), str(count)))
                closeness.append(closeness_list)
                with open(paths.PARAGRAPH_CONTENT_PATH + "{}/{}_{}".format(alias, text, count), "w", encoding="utf8") \
                        as content_file:
                    content_file.write(paragraph)
            pickle.dump(paragraph_list,
                        open(paths.POS_PATH + "/" + alias + "/" + text + ".p", "wb"))

    with open(paths.TEXT_META_PATH + "/all_meta", "w",
              encoding="utf8") as metafile:
        metafile.write(",".join([x for x in files if x.endswith(".txt")]))
    pickle.dump(closeness,
                open(paths.CLOSENESS_PATH + "/" + alias + "/" + "closeness.p", "wb"))


def segment_into_sentences(text):
    # TODO
    return []


def extract_theutonista(texts, alias):
    closeness = []
    for text in texts:
        if not text.endswith(".txt"):
            # support different file types here
            continue
        with open(os.path.join(paths.TEXT_PATH, text), "r", encoding="utf8") as current_text:
            content = current_text.read()
            # split the text into paragraphs first
            sentences = segment_into_sentences(content)
            with open(os.path.join(paths.TEXT_META_PATH, f"{text}_meta"), "w", encoding="utf8") as metafile:
                metafile.write(f"PARAGRAPHS: {len(sentences)}")
            print(f"Current text: {text}")
            for count, sentence in enumerate(sentences):
                character2pos = extract_from_sentence_theutonista(sentence)
                closeness_list = calculate_weighted_distance_theutonista(count, character2pos)
                closeness.append(closeness_list)
                with open(os.path.join(paths.PARAGRAPH_CONTENT_PATH, alias, f"{text}_{count}"), "w", encoding="utf8") \
                        as f:
                    f.write(sentence)
    with open(os.path.join(paths.TEXT_META_PATH, "all_meta", "w"), encoding="utf8") as f:
        f.write(",".join([x for x in texts if x.endswith(".txt")]))
    pickle.dump(closeness, open(os.path.join(paths.CLOSENESS_PATH, alias, "closeness.p", "wb")))


def with_graphviz_output():
    """Runs extract_step with GraphvizOutput, producing a call graph of all functions."""
    graphviz = GraphvizOutput()
    graphviz.output_file = 'extract_step.png'

    with PyCallGraph(output=graphviz):
        make_folders()
        extract_step(language="english")


if __name__ == "__main__":
    # Alias.objects.get(identifier="cthulhu.txt").delete()
    # dragnmodels.Text.objects.get(name="cthulhu.txt").delete()
    make_folders(alias="/cthulhu.txt")
    extract_step_db(language="english", texts=["cthulhu.txt"], weight_threshold=0.75, distance_threshold=3)
    # extract_step(texts=["cthulhu.txt"], alias="/cthulhu.txt")
