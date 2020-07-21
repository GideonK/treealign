#!/usr/bin/python3

## This script creates folds for k-fold cross validation of tree alignment experiments using:
## - two TIGER-XML treebank files
## - a Stockholm TreeAligner (STA) style XML alignment file referring to these treebanks.

## It requires Python 3 and the lxml package (https://lxml.de/installation.html). It has not been tested on Python 2.

## Example commands:
# >>> python3 ten-fold.py -a ~/align/lit+law/exp/013ALM-270_normalized.xml -o ~/align/lit+law/folds
# >>> python3 ten-fold.py -a ~/align/lit+law/308_corpus-with-308/ALM-308_normalized.xml -o ~/align/lit+law/308_folds_corpus-with-308

## See end of document for more information.

import re
import sys
import os
import argparse
import logging
import math
import ntpath
from lxml import etree
from lxml import objectify
from copy import deepcopy
from pathlib import Path
from random import shuffle

lib_path = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'libs'))
sys.path.append(lib_path)
import tiger, sta, files

################
## CLASS OBJECTS
################
tiger_getinfo = tiger.GetInfo()
sta_getinfo = sta.GetInfo()
sta_files = sta.Files()
files_info = files.FileName()

##########
## GLOBALS
##########
snodes_in_sta = {}
tnodes_in_sta = {}
stree_has_alignments = {}
ttree_has_alignments = {}
aligned_sents = []
streepos = {}
ttreepos = {}

parser = argparse.ArgumentParser()
parser.add_argument("--align", "-a", help="Stockholm TreeAligner alignment file", required=True)
parser.add_argument("--outdir", "-o", help="Output directory", required=True)
parser.add_argument("--noshuffle", "-n", help="Do not shuffle extracted aligned sentences", action="store_true")
args = parser.parse_args()
treeparser = etree.XMLParser(remove_comments=True,recover=True)

try:
    align_tree = objectify.parse(args.align, parser=treeparser)
except IOError as e:
    logging.error("Unable to open STA-XML file (--align/-a) - does not exist or no read permissions.")

if not os.path.exists(args.outdir):
    logging.error("Specified output directory ("+args.outdir+") does not exist!")

abs_align = os.path.abspath(args.align)
tree_files = sta_files.get_treebank_files(align_tree,abs_align)

tree_files=sta_files.get_treebank_files(align_tree,abs_align)
if not tree_files:
    logging.error("Alignment file does not refer to treebanks or refers to treebanks that do not exist!")
else:
    try:
        stree = objectify.parse(tree_files[0], parser=treeparser)
    except IOError as e:
        logging.error("Unable to open source-side treebank file (as discovered in STA-XML file) - does not exist or no read permissions.")
    try:
        stree_copy = objectify.parse(tree_files[0], parser=treeparser)
    except IOError as e:
        logging.error("Unable to open source-side treebank file (as discovered in STA-XML file) - does not exist or no read permissions.")
    try:
        ttree = objectify.parse(tree_files[1], parser=treeparser)
    except IOError as e:
        logging.error("Unable to open target-side treebank file (as discovered in STA-XML file) - does not exist or no read permissions.")
    try:
        ttree_copy = objectify.parse(tree_files[1], parser=treeparser)
    except IOError as e:
        logging.error("Unable to open target-side treebank file (as discovered in STA-XML file) - does not exist or no read permissions.")

print("Alignment file:",abs_align,file=sys.stderr)
print("Source tree file:",tree_files[0],file=sys.stderr)
print("Target tree file:",tree_files[1],file=sys.stderr)

align_root = align_tree.getroot()
sroot = stree.getroot()
troot = ttree.getroot()
sroot_copy = stree_copy.getroot()
troot_copy = ttree_copy.getroot()

alignments = sta_getinfo.get_node_pairs(align_tree)

snodes = tiger_getinfo.link_nodes_to_sentids(stree)
tnodes = tiger_getinfo.link_nodes_to_sentids(ttree)

## Append all sentence pairs that are aligned in STA-XML to a list
for i in alignments:
    nodes = re.split(';',i)
    snodes_in_sta[nodes[0]] = 1
    tnodes_in_sta[nodes[1]] = 1
    alignment = snodes[nodes[0]]+";"+tnodes[nodes[1]] ## sentence alignment
    if alignment not in aligned_sents:
        aligned_sents.append(alignment)

for node in snodes:
    if node in snodes_in_sta:
        sentid = snodes[node]
        stree_has_alignments[sentid] = 1

for node in tnodes:
    if node in tnodes_in_sta:
        sentid = tnodes[node]
        ttree_has_alignments[sentid] = 1

sids = tiger_getinfo.get_sent_ids(stree)
tids = tiger_getinfo.get_sent_ids(ttree)

for i in sids:
    if not stree_has_alignments[i]:
        logging.warning("No terminal or nonterminal nodes of source-side sentence ID "+i+" appear in the alignment file!")

for i in tids:
    if not ttree_has_alignments[i]:
        logging.warning("No terminal or nonterminal nodes of target-side sentence ID "+i+" appear in the alignment file!")

sbody = sroot[1] ## <body>
sbody_copy = sroot_copy[1]
tbody = troot[1]
tbody_copy = troot_copy[1]

if not args.noshuffle:
    shuffle(aligned_sents)

## Remove body containing sentences, to be replaced
    sroot_copy.remove(sbody_copy)
## Create new body for sentences
    new_sbody = etree.SubElement(sroot_copy, "body")

    troot_copy.remove(tbody_copy)
    new_tbody = etree.SubElement(troot_copy, "body")

    for s in sbody:
        sid = s.attrib['id']
        spos = sbody.index(s) ## e.g. if it's the 3rd sentence, it will have the value 3, even if it has s2000
        streepos[sid] = spos ## e.g. the position of ID s2000 will be 3
    for s in tbody:
        tid = s.attrib['id']
        tpos = tbody.index(s)
        ttreepos[tid] = tpos

    for a in aligned_sents:
        nodes = re.split(';',a)
        sid = nodes[0]
        tid = nodes[1]
        shufpos = aligned_sents.index(a) ## the actual position of e.g. s163;s163 in the shuffled alignments (e.g. 3)
## Get real <s>
        ss_to_write = sbody[streepos[sid]] ## if sid (from the randomized list aligned_sents) is s163, it will check what is the position of s163 in the treebank. It will then take whatever it is in that position (perhaps s300) for writing next. This way, it follows the randomized list.
        ts_to_write = tbody[ttreepos[tid]]
        new_sbody.append( deepcopy(ss_to_write) )
        new_tbody.append( deepcopy(ts_to_write) )

stree_stem = files_info.getExtendedStem(tree_files[0])
ttree_stem = files_info.getExtendedStem(tree_files[1])

def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier
# https://realpython.com/python-rounding/#rounding-down

## Splitting up TIGER-XML files into folds

nr_sents = len(aligned_sents)
rdown = int(round_down(nr_sents,-1)) ## e.g. 273 becomes 270, 308 becomes 300
rdiff = nr_sents-rdown ## the difference, e.g. 3. We will spread them out across sets. E.g. 28, 28, 28, 27, 27, 27, 27, 27, 27.
foldsize = int(rdown/10) ## e.g. 27
train_fold = []
train_folds = []
test_folds = []
test_folds = []

pointer = 0
for i in range(0,10):
    train_fold = []
    test_fold = []
    if rdiff > 0:
        curfoldsize=foldsize+1 ## e.g. 28
    else:
        curfoldsize=foldsize ## e.g. 27
    if pointer == 0: ## first fold
        for j in range(0,curfoldsize):
            test_fold.append(aligned_sents[j])
        for j in range(curfoldsize,len(aligned_sents)):
            train_fold.append(aligned_sents[j])
    else:
        for j in range(0,pointer):
            train_fold.append(aligned_sents[j])
        for j in range(pointer,pointer+curfoldsize):
            test_fold.append(aligned_sents[j])
        if pointer+curfoldsize < len(aligned_sents):
            for j in range(pointer+curfoldsize,len(aligned_sents)):
                train_fold.append(aligned_sents[j])
    # for r in rest:
    #     train_fold.append(r)
    # for m in move_to_end:
    #     test_folds.append(m)
    train_folds.append(train_fold)
    test_folds.append(test_fold)
    # folds.append(fold)
    pointer = pointer+curfoldsize
    rdiff = rdiff-1

def replace_treebank_sents_with_fold(treebank_el,fold,side):
## A fold is a list of sentence ID pairs (e.g. "1;1", "2;2", etc.)
## Since we are going to change the copy of the treebank object, we have to create a new copy for each new fold.
    tree_copy = deepcopy(treebank_el)
    root_copy = tree_copy.getroot()
    body_copy = root_copy[1]
## Remove body containing sentences, to be replaced
    root_copy.remove(body_copy)
## Create new body for sub-sentences
    new_body = etree.SubElement(root_copy, "body")
    for f in fold:
        nodes = re.split(';',f)
        if side == 0:
            id = nodes[0]
            body = sbody
            treepos = streepos
        elif side == 1:
            id = nodes[1]
            body = tbody
            treepos = ttreepos
        pos = fold.index(f)
## Get real <s>
        to_write = body[treepos[id]]
        new_body.append(deepcopy(to_write))
    return tree_copy

def fold_to_lists(fold):
    sids = []
    tids = []
    for f in fold:
        ids = re.split(';',f)
        sids.append(ids[0])
        tids.append(ids[1])
    return sids,tids

def replace_align_sents_with_fold(atree,fold):
## A fold is a list of sentence ID pairs (e.g. "1;1", "2;2", etc.)
## Since we are going to change the copy of the alignment object, we have to create a new copy for each new fold.
    align_copy = deepcopy(atree)
    root_copy = align_copy.getroot()
    alignments_copy = root_copy[1]
    (sids,tids) = fold_to_lists(fold)
    for align in alignments_copy:
        sid = align[0].attrib['node_id']
        tid = align[1].attrib['node_id']
        ssentid = re.sub("(s[0-9]+)_.*","\\1",sid)
        tsentid = re.sub("(s[0-9]+)_.*","\\1",tid)
        if ssentid not in sids or tsentid not in tids:
            alignments_copy.remove(align)
    return align_copy

def test_output(treebank_file,fold,side):
## The position of each sentence alignment in the fold must correspond to the position of the sentence in the treebank.
    tree = objectify.parse(treebank_file, parser=treeparser)
    body = tree.findall('.//body')
    for s in body[0]:
        treepos = body[0].index(s)
        tree_id = s.attrib['id']
        fold_alignments = re.split(';',fold[treepos])
        if side == 0:
            fold_id = fold_alignments[0]
        elif side == 1:
            fold_id = fold_alignments[1]
        if tree_id != fold_id:
            if side == 0:
                print_side = "source"
            elif side == 1:
                print_side = "target"
            logging.error("We have found a case where the ID in the fold is not the same as the ID in a %s-side tree in the same position!\n  File: %s\n  Position: %s\n  Treebank sentence ID: %s\n  Fold sentence ID: %s" % (print_side, treebank_file, treepos, tree_id, fold_id))

align_stem = files_info.getExtendedStem(ntpath.basename(abs_align))
stree_stem = ntpath.basename(stree_stem)
ttree_stem = ntpath.basename(ttree_stem)

for i in range(1,len(train_folds)+1):
    strain_file = stree_stem+".rand"+str(i)+".train.xml"
    ttrain_file = ttree_stem+".rand"+str(i)+".train.xml"
    train_align_file = align_stem+".rand"+str(i)+".train.xml"
    stest_file = stree_stem+".rand"+str(i)+".test.xml"
    ttest_file = ttree_stem+".rand"+str(i)+".test.xml"
    test_align_file = align_stem+".rand"+str(i)+".test.xml"
# ## Now, we first write the sentences in both treebanks in the order in which they appear in the folds.
## WRITE TRAINING
    fold = train_folds[i-1]
    new_train_copy = replace_treebank_sents_with_fold(stree,fold,0)
    with open(args.outdir+"/"+strain_file,"bw+") as file:
        print ("Writing to",args.outdir+"/"+strain_file,file=sys.stderr)
        file.write(etree.tostring(new_train_copy, pretty_print=True, encoding="UTF-8"))
#         # print ("Testing output...",file=sys.stderr)
#         # test_output(args.outdir+"/"+stree_file,fold,0)
    new_train_copy = replace_treebank_sents_with_fold(ttree,fold,1)
    with open(args.outdir+"/"+ttrain_file,"bw+") as file:
        print("Writing to",args.outdir+"/"+ttrain_file,file=sys.stderr)
        file.write(etree.tostring(new_train_copy, pretty_print=True, encoding="UTF-8"))
    new_align_copy = replace_align_sents_with_fold(align_tree,fold)
    treebank_el1 = new_align_copy.findall('.//treebank')[0]
    treebank_el2 = new_align_copy.findall('.//treebank')[1]
    treebank_el1.attrib['filename'] = strain_file
    treebank_el2.attrib['filename'] = ttrain_file
    with open(args.outdir+"/"+train_align_file,"bw+") as file:
        print("Writing to",args.outdir+"/"+train_align_file,file=sys.stderr)
        file.write(etree.tostring(new_align_copy, pretty_print=True, encoding="UTF-8"))
## WRITE TESTING
    fold = test_folds[i-1]
    new_test_copy = replace_treebank_sents_with_fold(stree,fold,0)
    with open(args.outdir+"/"+stest_file,"bw+") as file:
        print ("Writing to",args.outdir+"/"+stest_file,file=sys.stderr)
        file.write(etree.tostring(new_test_copy, pretty_print=True, encoding="UTF-8"))
    new_test_copy = replace_treebank_sents_with_fold(ttree,fold,1)
    with open(args.outdir+"/"+ttest_file,"bw+") as file:
        print("Writing to",args.outdir+"/"+ttest_file,file=sys.stderr)
        file.write(etree.tostring(new_test_copy, pretty_print=True, encoding="UTF-8"))
    new_align_copy = replace_align_sents_with_fold(align_tree,fold)
    treebank_el1 = new_align_copy.findall('.//treebank')[0]
    treebank_el2 = new_align_copy.findall('.//treebank')[1]
    treebank_el1.attrib['filename'] = stest_file
    treebank_el2.attrib['filename'] = ttest_file
    with open(args.outdir+"/"+test_align_file,"bw+") as file:
        print("Writing to",args.outdir+"/"+test_align_file,file=sys.stderr)
        file.write(etree.tostring(new_align_copy, pretty_print=True, encoding="UTF-8"))

## Writing folds with sentence ID pairs to output for validation.
train_lines = []
test_lines = []
for fold in train_folds:
    line = ""
    for f in fold:
        line = line+f+" "
    line = line.rstrip()
    train_lines.append(line)
    train_lines.append("\n")
for fold in test_folds:
    line = ""
    for f in fold:
        line = line+f+" "
    line = line.rstrip()
    test_lines.append(line)
    test_lines.append("\n")

with open("train_folds.txt", "w+") as file:
    for l in train_lines:
        file.write(l)
with open("test_folds.txt", "w+") as file:
    for l in test_lines:
        file.write(l)

# =============
# DOCUMENTATION
# =============

## Keeping to convention, the alignment set is randomised first. Afterwards, nine copies are made of the randomised set so that it comprises ten sets in total. Each set is split up into ten parts, called folds, of equal size, where the tenth fold consists of a different part for each set. Numerically, the ten set can be presented as follows:

## Set 1: 1 2 3 4 5 6 7 8 9 10
## Set 2: 2 3 4 5 6 7 8 9 10 1
## Set 3: 1 3 4 5 6 7 8 9 10 2
## Set 4: 1 2 4 5 6 7 8 9 10 3
## Set 5: 1 2 3 5 6 7 8 9 10 4
## etc.
## such that eventually, all folds, 1 up to 10, appear as the tenth fold for one particular set.

## Then, for each set, an alignment model is trained on the first 9 folds, while the 10th fold (which is different for each set), is held out for testing.
## This ensures that all sentence pairs can used for both training and testing in a consistent, non-biased way.
## Any tree aligner of your choice should suffice. Lingua-Align (https://bitbucket.org/tiedemann/lingua-align/wiki/Home) was used in the extrinsic testing of this script.
## Instead of ten folds, a different number can be used (k-fold cross validation). This script is yet to be adapted for this, but the same principles hold.

## If the alignment set cannot be divided into exactly ten folds, we keep the sizes of the different folds as similar as possible. So for example, if we have an alignment set with 102 sentence pairs, for each copy, the sizes of the ten folds are:
## Copy 1: 10
## Copy 2: 10
## Copy 3: 10
## Copy 4: 10
## Copy 5: 10
## Copy 6: 10
## Copy 7: 10
## Copy 8: 10
## Copy 9: 11
## Copy 10: 11

## This, however, means that the sizes of the training and test sets of any given copy can differ from the sizes of those of other copies. Because of this, we have decided to physically split up the created training and test sets, so that it is obvious which is which.

## The script implements the ten-fold cross validation as follows:
# - The sentences in both TIGER-XML files are randomised in the same way.
# -- Before randomisation, we remove any sentences that are not referred to by the alignment file to make sure the real size of the folds stay the same. NOTE: At the moment, only a warning is displayed. (TODO)
# -- We obtain a list of the sentence alignments as implicated by the STA-XML, and randomise the list. The randomised list is then read to randomise the actual sentences in the TIGER-XML.
# - We then calculate the size of each fold, and then create folds for the treebanks. We create the same folds for the alignment file to fit with the treebank folds, as the header in each alignment file must refer to the correct file names of the copies made from the treebank files.
## - Set copies are numbered and saved to a specified directory, where an external script can run the cross validation.

## TODO:
# - Split alignment training and testing in one step while removing elements, instead of in two steps (i.e. not creating an object twice).
