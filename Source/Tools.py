'''
To do:
- genres
- MONGO PY!!!

@author: ozbolt
'''

import json, re
from time import sleep

########################
###  Config Folders  ###
########################
_RELEASERS = "../config/releasers.json"
TORRENT_WEBSITES = "../config/torrentSites.json"
URLS_LOCK = "../config/urlsLock.json"

def trailerCheck(str1, str2, year = ""):
    str1 = str1.lower().replace(" ", "")
    str2 = str2.lower().replace(" ", "").replace("hq", "").replace("hd", "").replace(str(year), "").replace("original", "")
    
    cmp = strCmp(str1, str2) 
    #print("cmp:", cmp, ": ", str2)
    return cmp

def strCmp(str1, str2, lower = False):
    if lower:
        str1 = str1.lower()
        str2 = str2.lower()
    dl = _dameraulevenshtein(str1, str2)
    siz = max(len(str1), len(str2))
    return 1-dl/siz

def checkLock_andLock(netloc, check = True):
    
    while True:
        try: #if 2 reads at once
            f = open(URLS_LOCK, "r")
            locks = json.load(f)
            f.close()
            break
        except:
            sleep(0.01)
    
    
    if (netloc in locks) and (check == True):
        lock = locks[netloc]
    else:
        lock = False
        
    if not lock:
        f = open(URLS_LOCK, "w")
        locks[netloc] = True
        json.dump(locks, f)
        f.close()
    
    return lock

def lockUrl(netloc):
    checkLock_andLock(netloc, check = False)
    

def getReleaser(movieTitle, releaseName):
        ###add if movie title is non ascii exception
        if not _isAscii(releaseName):
            return None
        
        f = open(_RELEASERS)
        releasers = json.load(f)
        f.close()
        
        for r in releasers[0]:
            if r in movieTitle:
                continue
            if r in releaseName:
                return r
            
        for p,r in releasers[1].items():
            if re.search(p, releaseName):
                return r
        
        for r in releasers[2]:
            if r in movieTitle:
                continue
            if r in releaseName:
                return r
        
        for r in releasers[3]:
            if r in releaseName:
                return None
        
        return "UNKNOWN release: #%s#" % releaseName

def _isAscii(s):
    return all(ord(c) < 128 for c in s)

def _dameraulevenshtein(seq1, seq2):
    '''
    Calculate the Damerau-Levenshtein distance between sequences.
    
    This distance is the number of additions, deletions, substitutions,
    and transpositions needed to transform the first sequence into the
    second. Although generally used with strings, any sequences of
    comparable objects will work.
    
    Transpositions are exchanges of *consecutive* characters; all other
    operations are self-explanatory.
    
    This implementation is O(N*M) time and O(M) space, for N and M the
    lengths of the two sequences.
    
    >>> dameraulevenshtein('ba', 'abc')
    2
    >>> dameraulevenshtein('fee', 'deed')
    2
    
    It works with arbitrary sequences too:
    >>> dameraulevenshtein('abcd', ['b', 'a', 'c', 'd', 'e'])
    2
    
    Got it from: http://code.activestate.com/recipes/576874-levenshtein-distance/
    Licensed under: MIT opensource license
    '''
    # codesnippet:D0DE4716-B6E6-4161-9219-2903BF8F547F
    # Conceptually, this is based on a len(seq1) + 1 * len(seq2) + 1 matrix.
    # However, only the current and two previous rows are needed at once,
    # so we only store those.
    oneago = None
    thisrow = list(range(1, len(seq2) + 1)) + [0]
    for x in range(len(seq1)):
        # Python lists wrap around for negative indices, so put the
        # leftmost column at the *end* of the list. This matches with
        # the zero-indexed strings and saves extra calculation.
        twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
        for y in range(len(seq2)):
            delcost = oneago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = oneago[y - 1] + (seq1[x] != seq2[y])
            thisrow[y] = min(delcost, addcost, subcost)
            # This block deals with transpositions
            if (x > 0 and y > 0 and seq1[x] == seq2[y - 1]
                and seq1[x-1] == seq2[y] and seq1[x] != seq2[y]):
                thisrow[y] = min(thisrow[y], twoago[y - 2] + 1)
    return thisrow[len(seq2) - 1]
    