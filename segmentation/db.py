from collections import defaultdict
from pprint import pprint

import MySQLdb

from sprachatlas.settings import WIKIPEDIA_DB_USER, WIKIPEDIA_DB_PASSWORD


def get_total_words_count_wikipedia():
    """
    Gets the total size of the dictionary for Wikipedia.

    :return:
    """
    HOST = "127.0.0.1"
    USER = WIKIPEDIA_DB_USER
    PASSWORD = WIKIPEDIA_DB_PASSWORD
    DB = "bar_wikipedia_2016_30K"
    db = MySQLdb.connect(host=HOST, user=USER, password=PASSWORD, db=DB)
    dbc = db.cursor(MySQLdb.cursors.DictCursor)
    dbc.execute("SELECT COUNT(*) AS c FROM words")
    for row in dbc.fetchall():
        return row["c"]


def get_wordcounts_bavarian(words=None, ignore_case=True):
    """
    Extracts word frequencies for words from the Wikipedia word frequency database.

    :param words: A list of words.
    :param ignore_case: Optional. Default: True. Whether the case should be ignored.
    :return: A dictionary mapping the words to their frequency.
    """
    HOST = "127.0.0.1"
    USER = WIKIPEDIA_DB_USER
    PASSWORD = WIKIPEDIA_DB_PASSWORD
    DB = "bar_wikipedia_2016_30K"
    db = MySQLdb.connect(host=HOST, user=USER, password=PASSWORD, db=DB)
    dbc = db.cursor(MySQLdb.cursors.DictCursor)
    db.set_character_set('utf8mb4')
    dbc.execute('SET NAMES utf8mb4;')
    dbc.execute('SET CHARACTER SET utf8mb4;')
    dbc.execute('SET character_set_connection=utf8mb4;')
    if words:
        format_strings = ",".join(["%s"] * len(words))
        dbc.execute("SELECT * FROM words WHERE lower(word) IN (%s)" % format_strings, words)
    else:
        dbc.execute("SELECT * FROM words")
    freq = defaultdict(int)
    for row in dbc.fetchall():
        row_dict = defaultdict(int, row)
        if ignore_case:
            word = row_dict["word"].lower()
        else:
            word = row_dict["word"]
        row_freq = row_dict["freq"]
        word_freq = int(freq[word])
        freq[word] = row_freq if row_freq > word_freq else word_freq
    dbc.execute("SELECT COUNT(freq) as c FROM words")
    return freq


def augment_freqs(d):
    # add all words that are missing from wikipedia but we encounter here
    with open("E:\PycharmProjects\sprachatlas\segmentation\word_augment.txt", "r") as f:
        cc = f.read().split("\n")
    for c in cc:
        d[c] = 100
    return d


def bavarian_frequencies(ignore_case=True):
    d = get_wordcounts_bavarian()
    d = augment_freqs(d)
    return [x for x, _ in sorted(d.items(), key=lambda k: k[1], reverse=True)]


if __name__ == "__main__":
    freqs = get_wordcounts_bavarian()
    # print(freqs["stückl"])
    freqs_rank = sorted(freqs.items(), key=lambda k: k[1], reverse=True)
    pprint(freqs_rank[:100])