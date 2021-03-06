"""
23 Jan 2013

functions to align contact maps.
Algorithm based on:
Di Lena, P., Fariselli, P., Margara, L., Vassura, M., & Casadio, R. (2010). 
Fast overlapping of protein contact maps by alignment of eigenvectors. 
Bioinformatics (Oxford, England), 26(18), 2250-8. doi:10.1093/bioinformatics/btq402

"""

from numpy        import array, sqrt
from numpy        import min as npmin
from numpy        import max as npmax
from numpy        import sum as npsum
from numpy        import mean
from numpy.linalg import eigh # eigh is for symmetric matrices
from scipy.stats  import spearmanr
from itertools    import product
from itertools    import combinations_with_replacement as combinations
from copy         import deepcopy

# for aleigen:
from numpy import median

import re
from subprocess import Popen, PIPE


def _sort_match(matches):
    return sorted([(a, b) for a, b in enumerate(matches)],
                  key=lambda x: x[1], reverse=True)

def core_nw_long(p_scores, penalty, l_p1, l_p2):
    """
    Core of the Needleman-Wunsch algorithm 
    """
    scores = virgin_score(penalty, l_p1 + 1, l_p2 + 1)
    ins = rmv = 0
    lpen = 4
    # pens=[penalty-penalty*(1-1/exp(i**2)) for i in xrange(0, 2 * (lpen+ 1),2)]
    pens = [penalty - penalty / (2 * lpen) * i for i in xrange(lpen + 1)] # BEST
    # pens = [penalty, penalty, penalty, penalty/1.2, 0]
    # pens = [penalty, penalty*1.5, penalty*2, penalty, penalty]
    for i in xrange(1, l_p1 + 1):
        for j in xrange(1, l_p2 + 1):
            mmax = max((ins, rmv))
            match  = p_scores[i - 1][j - 1] + scores[i - 1][j - 1]
            insert = scores[i - 1][j] + pens[mmax]
            delete = scores[i][j - 1] + pens[mmax]
            tmp = _sort_match((match, insert, delete))
            if tmp[0][0] == 1:
                if ins < lpen:
                    ins += 1
                rmv = 0
            elif tmp[0][0] == 2:
                if rmv < lpen:
                    rmv += 1
                ins = 0
            else:
                ins = rmv = 0
            scores[i][j] = tmp[0][1]
    align1 = []
    align2 = []
    i = l_p1 
    j = l_p2
    while i and j:
        score = scores[i][j]
        value = scores[i - 1][j - 1] + p_scores[i - 1][j - 1]
        if equal(score, value):
            i -= 1
            j -= 1
            align1.insert(0, i)
            align2.insert(0, j)
            ins = rmv = 0
            continue
        if equal(score, scores[i - 1][j] + pens[0]):
            i -= 1
            align1.insert(0, i)
            align2.insert(0, '-')
            continue
        if equal(score, scores[i][j - 1] + pens[0]):
            j -= 1
            align1.insert(0, '-')
            align2.insert(0, j)
            continue
        if equal(score, scores[i - 1][j] + pens[1]):
            i -= 1
            align1.insert(0, i)
            align2.insert(0, '-')
            continue
        if equal(score, scores[i][j - 1] + pens[1]):
            j -= 1
            align1.insert(0, '-')
            align2.insert(0, j)
            continue
        if equal(score, scores[i - 1][j] + pens[2]):
            i -= 1
            align1.insert(0, i)
            align2.insert(0, '-')
            continue
        if equal(score, scores[i][j - 1] + pens[2]):
            j -= 1
            align1.insert(0, '-')
            align2.insert(0, j)
            continue
        if equal(score, scores[i - 1][j] + pens[3]):
            i -= 1
            align1.insert(0, i)
            align2.insert(0, '-')
            continue
        if equal(score, scores[i][j - 1] + pens[3]):
            j -= 1
            align1.insert(0, '-')
            align2.insert(0, j)
            continue
        if equal(score, scores[i - 1][j] + pens[4]):
            i -= 1
            align1.insert(0, i)
            align2.insert(0, '-')
            continue
        if equal(score, scores[i][j - 1] + pens[4]):
            j -= 1
            align1.insert(0, '-')
            align2.insert(0, j)
            continue
        print score
        print value
        print scores[i-1][j]
        print scores[i][j-1]
        print penalty, ins, rmv
        for scr in scores:
            print ' '.join(['%7s' % (round(y, 4)) for y in scr])
        raise Exception('Something  is failing and it is my fault...')
    return align1, align2, scores[i][j]


def core_nw(p_scores, penalty, l_p1, l_p2):
    """
    Core of the Needleman-Wunsch algorithm 
    """
    scores = virgin_score(penalty, l_p1 + 1, l_p2 + 1)
    for i in xrange(1, l_p1 + 1):
        for j in xrange(1, l_p2 + 1):
            match  = p_scores[i - 1][j - 1] + scores[i - 1][j - 1]
            insert = scores[i - 1][j] + penalty
            delete = scores[i][j - 1] + penalty
            scores[i][j] = max((match, insert, delete))
    align1 = []
    align2 = []
    i = l_p1 
    j = l_p2 
    while i and j:
        score = scores[i][j]
        value = scores[i - 1][j - 1] + p_scores[i - 1][j - 1]
        if equal(score, value):
            i -= 1
            j -= 1
            align1.insert(0, i)
            align2.insert(0, j)
        elif equal(score, scores[i - 1][j] + penalty):
            i -= 1
            align1.insert(0, i)
            align2.insert(0, '-')
        elif equal(score, scores[i][j - 1] + penalty):
            j -= 1
            align1.insert(0, '-')
            align2.insert(0, j)
        else:
            for scr in scores:
                print ' '.join(['%7s' % (round(y, 4)) for y in scr])
            raise Exception('Something  is failing and it is my fault...')
    return align1, align2, scores[i][j]


def equal(a, b, cut_off=1e-9):
    """
    Equality for floats
    """
    return abs(a - b) < cut_off


def optimal_cmo(hic1, hic2, num_v=None, max_num_v=None, verbose=False,
                method='frobenius', long_nw=True, long_dist=True):
    """

    Note: penalty is defined as the minimum value of the pre-scoring matrix.
    
    :param hic1: first matrix to align
    :param hic2: second matrix to align
    :param None num_v: number of eigen vectors to consider, max is:
        max(min(len(hic1), len(hic2)))
    :param None max_num_v: maximum number of eigen vectors to consider.
    :param score method: distance function to use as alignment score. if 'score'
       distance will be the result of the last value of the Needleman-Wunsch
       algorithm. If 'frobenius' a modification of the Frobenius distance will
       be used

    :returns: two lists, one per aligned matrix, plus a dict summarizing the
        goodness of the alignment with the distance between matrices, their 
        Spearman correlation Rho value and pvalue.
    """

    l_p1 = len(hic1)
    l_p2 = len(hic2)
    num_v = num_v or min(l_p1, l_p2)
    if max_num_v:
        num_v = min(max_num_v, num_v)
    if num_v > l_p1 or num_v > l_p2:
        raise Exception('\nnum_v should be at most %s\n' % (min(l_p1, l_p2)))
    val1, vec1 = eigh(hic1)
    if npsum(vec1).imag:
        raise Exception("ERROR: Hi-C data is not symmetric.\n" +
                        '%s\n\n%s' % (hic1, vec1))
    val2, vec2 = eigh(hic2)
    if npsum(vec2).imag:
        raise Exception("ERROR: Hi-C data is not symmetric.\n" +
                        '%s\n\n%s' % (hic2, vec2))
    #
    val1 = array([sqrt(abs(v)) for v in val1])
    val2 = array([sqrt(abs(v)) for v in val2])
    idx = val1.argsort()[::-1]
    val1 = val1[idx]
    vec1 = vec1[idx]
    idx = val2.argsort()[::-1]
    val2 = val2[idx]
    vec2 = vec2[idx]
    #
    vec1 = array([val1[i] * vec1[:, i] for i in xrange(num_v)]).transpose()
    vec2 = array([val2[i] * vec2[:, i] for i in xrange(num_v)]).transpose()
    nearest = float('inf')
    nw = core_nw_long if long_nw else core_nw
    dister = get_dist_long if long_dist else get_dist
    best_alis = []
    for num in xrange(1, num_v + 1):
        for factors in product([1, -1], repeat=num):
            vec1p = factors * vec1[:, :num]
            vec2p = vec2[:, :num]
            p_scores = prescoring(vec1p, vec2p, l_p1, l_p2)
            penalty = min([npmin(p_scores)] + [-npmax(p_scores)])
            align1, align2, dist = nw(p_scores, penalty, l_p1, l_p2)
            try:
                if method == 'frobenius':
                    dist = dister(align1, align2, hic1, hic2)
                else:
                    dist = -dist
                if dist < nearest:
                    if not penalty:
                        for scr in p_scores:
                            print ' '.join(['%7s' % (round(y, 2)) for y in scr])
                    nearest = dist
                    best_alis = [align1, align2]
                    best_pen = penalty
            except IndexError as e:
                print e
                pass
    try:
        align1, align2 = best_alis
    except ValueError:
        pass
    if verbose:
        print '\n Alignment (score = %s):' % (nearest)
        print 'TADS 1: '+'|'.join(['%4s' % (str(int(x)) \
                                            if x!='-' else '-'*3) for x in align1])
        print 'TADS 2: '+'|'.join(['%4s' % (str(int(x)) \
                                            if x!='-' else '-'*3) for x in align2])
    rho, pval = get_score(align1, align2, hic1, hic2)
    # print best_pen
    if not best_pen:
        print 'WARNING: penalty NULL!!!\n\n'
    return align1, align2, {'dist': nearest, 'rho': rho, 'pval': pval}
    

def virgin_score(penalty, l_p1, l_p2):
    """
    Fill a matrix with zeros, except first row and first column filled with \
    multiple values of penalty.
    """
    zeros    = [0.0 for _ in xrange(l_p2)]
    return [[penalty * j for j in xrange(l_p2)]] + \
           [[penalty * i] + zeros for i in xrange(1, l_p1)]


def prescoring(vc1, vc2, l_p1, l_p2):
    """
    yes... this is the bottle neck, almost 2/3 of the time spent here
    """
    p_score = []
    for i in xrange(l_p1):
        vci = vc1[i].__mul__
        p_score.append([vci(vc2[j]).sum() for j in xrange(l_p2)])
    return p_score
    #return [[sum(vc1[i] * vc2[j]) for j in xrange(l_p2)] for i in xrange(l_p1)]


def get_dist(align1, align2, tad1, tad2):
    """
    Frobenius norm
    """
    map1 = []
    map2 = []
    for i, j in zip(align1, align2):
        if i != '-' and j != '-':
            map1.append(i)
            map2.append(j)
    pp1 = [tad1[i][j] for i, j in combinations(map1, 2)]
    pp2 = [tad2[i][j] for i, j in combinations(map2, 2)]
    return float(sum([(pp-pp2[p])**2 for p, pp in enumerate(pp1)]))\
           / (len(pp1)+1)


def get_dist_long(align1, align2, tad1, tad2):
    """
    Frobenius norm
    """
    map1 = []
    map2 = []
    pen  = ((float(mean(tad2)) + mean(tad1)) / 2) * len(align1)
    xpen = 0
    exti = extd = 1
    for i, j in zip(align1, align2):
        if i != '-' and j != '-':
            map1.append(i)
            map2.append(j)
            exti = extd = 1
        elif i == '-': # favour long gaps: stop penalizing if GAP lon enough
            xpen += pen / exti
            exti += 1
            extd = 1
        else:
            xpen += pen / extd
            extd += 1
            exti = 1
    pp1 = [tad1[i][j] for i, j in combinations(map1, 2)]
    pp2 = [tad2[i][j] for i, j in combinations(map2, 2)]
    return float(sum([(pp-pp2[p])**2 for p, pp in enumerate(pp1)]))\
           / (len(pp1)+1) + xpen


def get_score(align1, align2, tad1, tad2):
    """
    Using Spearman Rho correation value, between matrices.
    Computed only in half of the matrix, and without the diagonal
    
    """
    map1 = []
    map2 = []
    for i, j in zip(align1, align2):
        if j != '-' and i != '-':
            map1.append(i)
            map2.append(j)
    pp1 = [[tad1[i][j] for j in map1] for i in map1] # do not use 
    pp2 = [[tad2[i][j] for j in map2] for i in map2] # diagonal?
    return spearmanr(pp1, pp2, axis=None)


def get_OLD_score(align1, align2, p1, p2):
    """
    Original scoring function, based on contact map overlap.
    """
    map1 = []
    map2 = []
    for i, j in zip(align1, align2):
        if j != '-' and i != '-':
            map1.append(i)
            map2.append(j)
    com = len(map1)
    pp1 = [[p1[i][j] for j in map1] for i in map1]
    pp2 = [[p2[i][j] for j in map2] for i in map2]
    cm1 = sum([pp1[i][j] for i in xrange(com) for j in xrange(i + 1, com)])
    cm2 = sum([pp2[i][j] for i in xrange(com) for j in xrange(i + 1, com)])
    cmo = sum([1 - abs(pp2[i][j] - pp1[i][j]) \
               for i in xrange(com) for j in xrange(i + 1, com)])
    return float(2 * cmo)/(cm1+cm2)


###
# Following is for aleigen


def matrix2binnary_contacts(tad1, tad2):
    cutoff = median(tad1)
    contacts1 = []
    contacts2 = []
    for i in xrange(len(tad1)):
        for j in xrange(i, len(tad1)):
            if tad1[i][j] > cutoff:
                contacts1.append((i, j))
    cutoff = median(tad2)
    for i in xrange(len(tad2)):
        for j in xrange(i, len(tad2)):
            if tad2[i][j] > cutoff:
                contacts2.append((i, j))
    return contacts1, contacts2


def run_aleigen(contacts1, contacts2, num_v):
    """

    * c1, c2 = number of contacts of the first and seconf contact map
               (after removing non-matching columns/rows)
    * cmo = total number of matching contacts (above the first diagonal)
      of the computed overlap
    * score = 2*CMO/(C1+C2)

    """
    f_string = '/tmp/lala%s.txt'
    f_name1 = f_string % (1)
    f_name2 = f_string % (2)
    write_contacts(contacts1, contacts2, f_string)
    sc_str = re.compile('Score\s+C1\s+C2\s+CMO\n([0-9.]+)\s+[0-9]+\s+.*')
    out = Popen('aleigen %s %s %s' % (f_name1, f_name2, num_v),
                shell=True, stdout=PIPE).communicate()[0]
    score = [float(c) for c in re.findall(sc_str, out)]
    print out
    align1 = []
    align2 = []
    for line in out.split('\n')[2:]:
        if not re.match('[0-9]+\s+[0-9]+', line):
            continue
        el1, el2 = [int(c) for c in line.split()]
        align1.append(el1)
        align2.append(el2)
    return align1, align2, score


def write_contacts(contacts1, contacts2, f_string):
    for i, contacts in enumerate([contacts1, contacts2]):
        out = open(f_string % (i+1), 'w')
        out.write(str(max([max(c) for c in contacts])+1) + '\n')
        out.write('\n'.join([str(c1) + ' ' + str(c2) for c1, c2 in contacts]))
        out.write('\n')
        out.close()


def merge_tads(tad1, tad2, ali1, ali2):
    ali = []
    ali.append(deepcopy(ali1))
    ali.append(deepcopy(ali2))
    for i in xrange(max(ali1[0], ali2[0]) - 1, -1, -1):
        if ali[0][0]:
            ali1.insert(0, i)
            ali2.insert(0, '-')
        elif ali[1][0]:
            ali1.insert(0, '-')
            ali2.insert(0, i)
    size = len(ali1)
    matrix1 = [[0.1 for _ in xrange(size)] for _ in xrange(size)]
    matrix2 = [[0.1 for _ in xrange(size)] for _ in xrange(size)]
    matrixm = [[0.1 for _ in xrange(size)] for _ in xrange(size)]
    for i in xrange(size):
        if ali1[i] == '-' or ali2[i] == '-':
            matrixm[i] = [float('nan') for _ in xrange(size)]
            if ali1[i] == '-':
                matrix1[i]  = [float('nan') for _ in xrange(size)]
                matrix2[i]  = [tad2[ali2[i]][ali2[j]] \
                               if ali2[j] != '-' else float('nan')\
                               for j in xrange(size)]
            elif ali2[i] == '-':
                matrix2[i]  = [float('nan') for _ in xrange(size)]
                matrix1[i]  = [tad1[ali1[i]][ali1[j]] \
                               if ali1[j] != '-' else float('nan')\
                               for j in xrange(size)]
            continue
        for j in xrange(size):
            if ali1[j] == '-' or ali2[j] == '-':
                matrixm[i][j] = float('nan')
                if ali1[j] == '-':
                    matrix1[i][j] = float('nan')
                    matrix2[i][j]  = tad2[ali2[i]][ali2[j]]
                elif ali2[j] == '-':
                    matrix2[i][j] = float('nan')
                    matrix1[i][j] = tad1[ali1[i]][ali1[j]]
                continue
            matrix1[i][j]  = tad1[ali1[i]][ali1[j]]
            matrix2[i][j]  = tad2[ali2[i]][ali2[j]]
            matrixm[i][j]  = tad1[ali1[i]][ali1[j]]
            matrixm[i][j] += tad2[ali2[i]][ali2[j]]
            matrixm[i][j] /= 2
    return matrix1, matrix2, matrixm
