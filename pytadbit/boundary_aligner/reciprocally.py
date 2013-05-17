"""
02 Dec 2012

Aligner based on reciprocal closest hits for Topologically Associated Domains
"""


def find_closest(num, tads1, start=0):
    closest = 0
    diff = inf = float('inf')
    for n in tads1:
        if n < start: continue
        if abs(n - num) < diff:
            diff = abs(n - num)
            closest = n
        elif diff != inf:
            break
    return closest


def find_closest_reciprocal(t1, tads1, tads2, start=0):
    """
    function to check the needleman_wunsch algorithm.
    """
    closest = None
    diff = inf = float('inf')
    gap = 0
    for t2 in tads2:
        if t2 <= start: continue
        if abs(t2 - t1) < diff:
            t1prim = find_closest(t2, tads1, start=t1)
            if t1 == t1prim:
                if diff != inf:
                    gap += 1
                diff = abs(t2 - t1)
                closest = t2
        elif diff != inf:
            break
    if diff == inf:
        return '-', 0
    return closest, gap


def reciprocal(tads1, tads2, penalty=None, verbose=False, max_dist=100000):
    """
    Method based on reciprocal closest boundaries (bd). bd1 will be aligned
       with bd2 (closest boundary from bd1) if and only if bd1 is the closest
       boundary of bd2 too (and of course if the distance between bd1 and bd2 is
       lower than max_dist).

    :argument tads1: list of boundaries
    :argument tads2: list of boundaries
    :argument None penalty: if None, penalty will be calculated based on mean
       distances between boundaries (for the current alignment).
       FIXME: find something better.
    :argument verbose: print alignment
    :argument 100000 max_dist: distance threshold from which two boundaries can
       not be aligned together.
    """

    if not penalty:
        # set penalty to the average length of a TAD
        penalty  = float(reduce(lambda x, y: abs(x - y),
                                tads1)) / len(tads1)
        penalty += float(reduce(lambda x, y: abs(x - y),
                                tads2)) / len(tads2)
    start = 0
    diffs = []
    align1 = []
    align2 = []
    i = 0
    for t in tads1:
        closest, gap = find_closest_reciprocal(t, tads1, tads2,
                                               start=start)
        while gap > 0:
            try:
                align2.append(tads2[i])
            except IndexError:
                break
            align1.append('-')
            i += 1
            gap -= 1
        diff = penalty
        if closest != '-':
            start = closest
            diff  = abs(t - closest)
            if diff > max_dist:
                # print 'MAAAAX: ', t, closest, diff, max_dist
                if t > closest:
                    align2.append(closest)
                    i += 1
                    align1.append('-')
                    closest = '-'
                else:
                    align1.append(t)
                    align2.append('-')
                    t = '-'
                diff  = penalty
        diffs.append(diff)
        #print 't2i {}; start {}; t1 {}; clos {}; gap {}'.format(
        #    tads2[i], start, t, closest, gap)
        align1.append(t)
        align2.append(closest)
        if closest != '-':
            i += 1
    if verbose:
        print '\n Alignment:'
        print 'TADS 1: '+'|'.join(['%6s' % (str(int(x/1000)) if x!='-' else '-'*3) \
                                   for x in align1])
        print 'TADS 2: '+'|'.join(['%6s' % (str(int(x/1000)) if x!='-' else '-'*3) \
                                   for x in align2])

    return [align1, align2], float(sum(diffs))/len(align1)
        
