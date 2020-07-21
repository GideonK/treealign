#!/usr/bin/python3
# -*- coding: utf-8 -*-

## Receives a parallel treebank in the following format:
## - STA-XML alignment file (Stockholm TreeAligner format)
## - Two treebanks in the source and target language, in TIGER-XML

## Reads the STA-XML and checks if all nodes in the STA-XML als occur in the TIGER-XML files.

## Usage:

# >>> python3 check-STA-align.py -a STA.xml [ -s source-tiger.xml ] [ -t target-tiger.xml ]

## Example use:

# >>> python3 check-STA-align.py -a ~/align/lit+law/308_corpus-with-308/ALM-308_normalized.xml -s ~/align/lit+law/308_corpus-with-308/308DE_LIT_LAW_normalized.xml -t ~/align/lit+law/308_corpus-with-308/308KA_LIT_LAW_normalized.xml
# Referenced treebanks exist and all alignments are valid.

## If -s and -t are not specified, the script will attempt to open the treebanks from the references in the STA-XML. Hence, this also works, as long as the source and target treebanks occur under separate <treebank> elements, in order, under the attribute "filename":

# >>> python3 check-STA-align.py -a ~/align/lit+law/308_corpus-with-308/ALM-308_normalized.xml

## It can appear like below, or using absolute or relative paths:

# <treebanks>
# <treebank id="de" language="de_DE" filename="308DE_LIT_LAW_normalized.xml"/>
# <treebank id="ka" language="ka_GE" filename="308KA_LIT_LAW_normalized.xml"/>
# </treebanks>

## Requires sta.py, tiger.py and data.py in ../../libs.
## Requires the lxml package and its dependencies. (https://lxml.de/installation.html)

import sys
import os
import argparse
from lxml import etree
from pathlib import Path
lib_path = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'libs'))
sys.path.append(lib_path)
import sta, tiger

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

## *** MAIN CODE ***
parser = argparse.ArgumentParser()
parser.add_argument("--align", "-a", help="Stockholm TreeAligner style alignment file", required=True)
parser.add_argument("--source", "-s", help="Source-side TIGER-XML file")
parser.add_argument("--target", "-t", help="Target-side TIGER-XML file")

## Parse arguments
args = parser.parse_args()

## Get tree objects of STA-XML
align_tree = etree.parse(args.align)

## Get object of Files class in sta.py
files = sta.Files()

## Get objects of Nodes class in tiger.py
source_nodes = tiger.GetInfo()
target_nodes = tiger.GetInfo()

def get_treebanks():
    ## Get absolute path of alignment file
    abs_input=os.path.abspath(args.align)
    filenames=files.get_treebank_files(align_tree,abs_input)
    if not filenames:
        eprint("At least one of the treebanks referred to in the alignment file does not exist!")
        sys.exit(1)
    else:
        stree = etree.parse(filenames[0])
        ttree = etree.parse(filenames[1])
        return filenames

if (not args.source or not args.target):
    (stree,ttree) = get_treebanks()
else:
    possible_stree=Path(args.source)
    possible_ttree=Path(args.target)
    if not possible_stree.is_file():
        eprint("check-STA-align.py: Specified source-side TIGER-XML file (args.source) does not exist!")
        sys.exit(1)
    else:
        stree = args.source
    if not possible_ttree.is_file():
        eprint("check-STA-align.py: Specified target-side TIGER-XML file (args.target) does not exist!")
        sys.exit(1)
    else:
        ttree = args.target

## Now that we know that the TIGER-XML trees exist, let's create objects for them.
source_tree = etree.parse(stree)
target_tree = etree.parse(ttree)

## Get all treebank IDs in dictionary format so we can quickly check them.
snodes = source_nodes.get_nodes(source_tree,"dict")
tnodes = target_nodes.get_nodes(target_tree,"dict")

is_ok = 1

## Now iterate through the STA-XML
align_root = align_tree.getroot()
for align in align_root.iter("align"):
    source_node = align[0]
    target_node = align[1]
    source_align_id = source_node.attrib['node_id']
    target_align_id = target_node.attrib['node_id']
    if source_align_id not in snodes:
        eprint ("The following source-side node ID, which is referenced by the alignment file, does not occur in the source-side tree! ",source_align_id)
        is_ok = 0
    if target_align_id not in tnodes:
        eprint ("The following target-side node ID, which is referenced by the alignment file, does not occur in the target-side tree! ",target_align_id)
        is_ok = 0

if is_ok == 1:
    eprint("Referenced treebanks exist and all alignments are valid.")
