from segmentation.db import bavarian_frequencies, get_wordcounts_bavarian
from segmentation.wordninja import segmentation


def teuthonista_to_string(raw):
    """
    Translates the Theutonista transcription string to regular strings of words, without the phonetics.
    :param raw: The raw Theutonista string.
    :return: A list of strings (words) that are contained in the string, separated only if there is a pause.
    """

    words = []
    processed = []
    for i, c in enumerate(raw.lower()):
        if c.isalpha():
            if c == "o" and processed[-1] == "a":
                processed.append("u")  # ao sounds like au
                continue
            if c == "x":  # ch-sounds
                processed.append("ch")  # and raw[i+1].isdigit() - probably always ch?
                continue
            if c == "s":  # sch-sounds, probably? TODO: figure out what S7 etc sound like
                if processed[-1] == "t":
                    del processed[-1]
                    processed.append("z")  # TODO: check if this works always!
                    continue
                elif raw[i+1].isdigit():
                    d = int(raw[i+1])
                    if d in [2, 8]:
                        processed.append("s")
                    elif d == 9:
                        processed.append("z")
                    else:
                        processed.append("sch")
                else:
                    processed.append("s")
                continue
            if c == "k" and raw[i+1].isdigit():
                d = int(raw[i+1])
                if d == 2:
                    processed.append("ck")
                continue
            if processed and processed[-1] == c and c in "aeiou":
                continue  # double vocals make no sense, maybe?
            processed.append(c)
        elif c == "(":
            if raw[i:i+3] == "(:)":
                words.append("".join(processed))
                processed = []  # way to deal with pauses
    words.append("".join(processed))
    return words


def teuthonista_split(raw):
    to_segment = teuthonista_to_string(raw)
    words = bavarian_frequencies()
    case = get_wordcounts_bavarian(ignore_case=False)
    freqs = get_wordcounts_bavarian()
    p = []
    for chunk in to_segment:
        segs = segmentation(chunk)
        skip = False
        for i, seg in enumerate(segs[:-1]):
            if skip:
                skip = False
                continue
            n = seg + segs[i + 1]
            if freqs[n] > freqs[seg]:
                seg = n
            current_freq = case[seg.title()]
            next_freq = case[segs[i + 1].title()]
            # if 0 < current_freq >= next_freq
            if (case[seg.title()] or case[seg]) \
                    and (case[segs[i + 1].title()] or case[segs[i + 1]]) \
                    and case[seg.title()] >= case[seg] \
                    and case[segs[i + 1].title()] >= case[segs[i + 1]] \
                    and len(seg) > 1 and len(segs[i + 1]) > 1:
                seg = n.title()
                skip = True
            p.append(seg)
        if not skip:
            p.append(segs[-1])
    return p


def get_theutonista_tail(raw, pos, i):
    tail = raw[pos+i+1:]
    for j, cc in enumerate(tail):
        if cc.isalpha():
            end = i+pos+j+1
            match = raw[pos:end]
            return match, end
    # if last word
    match = raw[pos:]
    return match, 0  # the 0 should not be used every, should be safe


def add_theutonista_to_segmented(raw, segmented):
    pos = 0
    done = {}
    raw = raw.lower()
    for word in segmented:
        word = word.lower()
        lastchar = word[-1]
        # special cases
        special = {
            "u": "ao",
            "ch": "x",
            "z": "ts s9",
            "s": "s2 s8",
            "sch": "any other s"
        }
        charcount = 0
        prevchar = ""
        next_seg = raw[pos:]
        for i, c in enumerate(next_seg):
            if c.isalpha():
                charcount += 1
                if c == lastchar and charcount >= len(word):
                    # done, get everything until next char
                    done[word], j = get_theutonista_tail(raw, pos, i)
                    pos = j
                    break
                else:
                    if c in "oxs":
                        if c == "o" and raw[pos-1] == "a":
                            done[word], j = get_theutonista_tail(raw, pos, i)
                            pos = j
                            break
                        elif c == "x" and word[-2:] == "ch":
                            done[word], j = get_theutonista_tail(raw, pos, i)
                            pos = j
                            break
                        elif c == "s" and lastchar == "z" and prevchar == "t":
                            done[word], j = get_theutonista_tail(raw, pos, i)
                            pos = j
                            break
            elif c.isdigit():
                if prevchar == "s":
                    if lastchar == "z" and c == "9":
                        done[word], j = get_theutonista_tail(raw, pos, i)
                        pos = j
                        break
                    elif word[-3:] == "sch" and c not in "289":
                        done[word], j = get_theutonista_tail(raw, pos, i)
                        pos = j
                        break
            prevchar = c
    return done


if __name__ == "__main__":
    t = "u5ntdo5-2ha2+-2nsda5nmi-2det1s2wo2-he2nta2+-2e2+(:)ts9a2k2"
    segs = teuthonista_split(t)
    w = add_theutonista_to_segmented(t, segs)
    print(w)
    raise Exception


    # t = "de2-2ho5-da2rex68d2a2gro5$o2s81ma-2o2lvo2-na,du5-2ndhi5nt1"
    # t = "de2-2ha5mde2+-2mt1ho2-sn4ao2f1a,gs7li5t1s2d2bi-sdo5ao2f1a,u5-ndu5nta,de2-2bru5-xs7do2+-2a2dri5n2a,d"
    t = "u5ntdo5-2ha2+-2nsda5nmi-2det1s2wo2-he2nta2+-2e2+(:)ts9a2k2"
    to_segment = teuthonista_to_string(t)
    words = bavarian_frequencies()
    with open("words_alphabetical.txt", "w", encoding="utf8") as f:
        f.write("\n".join(sorted(words)))
    case = get_wordcounts_bavarian(ignore_case=False)
    freqs = get_wordcounts_bavarian()
    for r in to_segment:
        segs = segmentation(r)
        print(f"SEGS: {segs}")
        p = []
        skip = False
        for i, seg in enumerate(segs[:-1]):
            if skip:
                skip = False
                continue
            n = seg + segs[i+1]
            if freqs[n] > freqs[seg]:
                seg = n
            current_freq = case[seg.title()]
            next_freq = case[segs[i + 1].title()]
            # if 0 < current_freq >= next_freq
            if (case[seg.title()] or case[seg]) \
                    and (case[segs[i+1].title()] or case[segs[i+1]]) \
                    and case[seg.title()] >= case[seg] \
                    and case[segs[i+1].title()] >= case[segs[i+1]] \
                    and len(seg) > 1 and len(segs[i+1]) > 1:
                seg = n.title()
                skip = True
            p.append(seg)
        if not skip:
            p.append(segs[-1])
        print(p)
        print("-----------")
