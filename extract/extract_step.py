#!/usr/bin/env python3
"""
Allows the execution of extract_step.
In this step the texts are pre-processed, they are tokenized and POS-tags are assigned.
"""
import os
import pickle

from extract.text_extract import character_to_position, \
    calculate_weighted_distance_theutonista
from sprachatlas import setup
setup()
from sprachatlas.settings import DRAGN_LINE_COMBINE


from util import paths


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


def make_folders(alias):
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


def segment_into_sentences(lines, size=DRAGN_LINE_COMBINE):
    chunks = [lines[i:i+size] for i in range(0, len(lines), size)]
    return chunks


def load_text(text):
    with open(os.path.join(paths.TEXT_PATH, text), "r", encoding="utf8") as current_text:
        lines = current_text.readlines()
    out = []
    for line in lines:
        try:
            start, end, content = line.split("\t")
            out.append((start, end, content))
        except ValueError:
            print(f"ERROR LINE: {line}")
    return out


def extract_theutonista(texts, alias):
    closeness = []
    for text in texts:
        if not text.endswith(".txt"):
            # support different file types here
            continue
        lines = load_text(text)
        sentences = segment_into_sentences(lines)
        with open(os.path.join(paths.TEXT_META_PATH, f"{text}_meta"), "w", encoding="utf8") as metafile:
            metafile.write(f"PARAGRAPHS: {len(sentences)}")
        print(f"Current text: {text}")
        for chunk_id, chunks in enumerate(sentences):
            print(f"-> PROCESSING CHUNK {chunk_id} OUT OF {len(sentences)}")
            # start = chunks[0][0]
            # end = chunks[-1][1]
            c_id = f"{text}_{chunk_id}"
            content = "".join([x[2] for x in chunks])
            character2pos = character_to_position(content)
            closeness_list = calculate_weighted_distance_theutonista(c_id, character2pos)
            closeness.append(closeness_list)
            paragraph_path = os.path.join(paths.PARAGRAPH_CONTENT_PATH, alias, f"{text}_{chunk_id}")
            with open(paragraph_path, "w", encoding="utf8") as f:
                f.write(content)
    with open(os.path.join(paths.TEXT_META_PATH, "all_meta"), "w", encoding="utf8") as f:
        f.write(",".join([x for x in texts if x.endswith(".txt")]))
    with open(os.path.join(paths.CLOSENESS_PATH, alias, "closeness.p"), "wb") as f:
        pickle.dump(closeness, f)


if __name__ == "__main__":
    # Alias.objects.get(identifier="cthulhu.txt").delete()
    # dragnmodels.Text.objects.get(name="cthulhu.txt").delete()
    # make_folders(alias="/cthulhu.txt")
    # extract_step_db(language="english", texts=["cthulhu.txt"], weight_threshold=0.75, distance_threshold=3)
    # extract_step(texts=["cthulhu.txt"], alias="/cthulhu.txt")
    t = ["t5.txt"]
    a = "t5.txt"
    # make_folders(a)
    extract_theutonista(t, a)