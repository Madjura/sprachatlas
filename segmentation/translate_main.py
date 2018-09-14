from segmentation.translate import teuthonista_split, add_theutonista_to_segmented

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
