from segmentation.db import bavarian_frequencies, get_wordcounts_bavarian
from segmentation.wordninja import segmentation


def teuthonista_to_string(raw):
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


if __name__ == "__main__":
    t = "de2-2ho5-da2rex68d2a2gro5$o2s81ma-2o2lvo2-na,du5-2ndhi5nt1"
    # t = "de2-2ha5mde2+-2mt1ho2-sn4ao2f1a,gs7li5t1s2d2bi-sdo5ao2f1a,u5-ndu5nta,de2-2bru5-xs7do2+-2a2dri5n2a,d"
    # t = "u5ntdo5-2ha2+-2nsda5nmi-2det1s2wo2-he2nta2+-2e2+(:)ts9a2k2"
    to_segment = teuthonista_to_string(t)
    words = bavarian_frequencies()
    with open("words_alphabetical.txt", "w") as f:
        f.write("\n".join(sorted(words)))
    case = get_wordcounts_bavarian(ignore_case=False)
    freqs = get_wordcounts_bavarian()
    for r in to_segment:
        segs = segmentation(r)
        print(r)
        print(segs)
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
