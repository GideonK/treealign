#!/usr/bin/python3

import re, os, logging, sys
from lxml import etree
from pathlib import Path
#lib_path = os.path.abspath(os.path.join(__file__, '..', '..', 'Python-libs'))
#sys.path.append(lib_path)
import files

# LXML tutorial:
# http://lxml.de/3.0/tutorial.html

class Files:
    def get_treebank_files(self,tree,alignment_file):
        files_info = files.FileName()
        treebanks = tree.findall('.//treebank')
        files_list=[]
        for x in treebanks:
            file=x.attrib['filename'] ## reference to source or target treebank in alignment file
            possible_file=Path(file)
            if possible_file.is_file(): ## check if file exists
                files_list.append(file)
            else: ## treebank file does not exist. The alignment file might refer to files within its directory without using an absolute path, so let's make sure.
                abs_file = files_info.check_absolute_path(file,os.path.dirname(os.path.realpath(alignment_file)))
                if abs_file != "":
                    files_list.append(abs_file)
                else:
                    print("File in treebank file (%s) not found!" % (abs_file), file=sys.stderr)
                    exit(1)
        return files_list

    def get_treebank_files_and_ids(self,tree,alignment_file):
        tree_to_id = {}
        id_to_tree = {}
        files = self.get_treebank_files(tree,alignment_file)
        treebanks = tree.findall('.//treebank')
        id = treebanks[0].get('id')
        id_to_tree[id] = files[0]
        id = treebanks[1].get('id')
        id_to_tree[id] = files[1]
        return id_to_tree

class GetInfo:
## ((
## Returns three dictionaries (hashes):
## - source_node[source_id] = target_id1;target_id2... ==> indicating an alignment between source and target IDs
## - target_node[target_id] = source_id1;source_id2... ==> the same, but with values and keys reversed
## - node_pair[source_id;target_id][type] = good

## One can build a dictionary of node pairs etc. but is it necessary? Find a way to access through tree object first.
## - node_pairnode_pair[source_id;target_id][last_change] = 2017-08-17
## - node_pairnode_pair[source_id;target_id][author] = OLEG
## - node_pairnode_pair[source_id;target_id]
## ))

    def get_node_pairs(self,tree):
## Returns a list of node pairs extracted from the alignment file in the following format:
## s158_7;s158_3
## s158_505;s158_508
## ...
        root = tree.getroot()
        nodes = []
#        alignments=root[1]
        for align in root.iter("align"):
            nodes.append("{};{}".format(align[0].attrib['node_id'],align[1].attrib['node_id']))
        return nodes

    def count_sent_pairs(self,tree,links_to_sentids1,links_to_sentids2):
## We might want to check if there are nodes that align to nodes in the other treebank that are represented by more than one sentence ID. We do the following:
## - Some sentences in a treebank may have nodes that differ with respect to the sentence IDs to which they refer. Using def link_nodes_to_sentids in tiger.py, we must therefore first construct a dictionary that links each node in the treebank to its real sentence ID. So even if a node itself has a different sentence ID than another one, it may still be linked to the same sentence ID. We use this link to determine sameness instead of just looking at the ID itself. For each tree, we require such a dictionary (links_to_sentids1 and links_to_sentids2).
## - Each alignment is noted as a sentence ID linked to another. Once a sentence ID that has already been linked is now linked to a different one, we record this.
## - If a node is not found in its dictionary, then we exit with an error.
        s2t = {}
        t2s = {}
        sorted_sents_combos = []
        source_count = 0
        target_count = 0
        root = tree.getroot()
        for align in root.iter("align"):
            s_id = align[0].get('node_id')
            t_id = align[1].get('node_id')

            if not s_id in links_to_sentids1:
                logging.warning("sta.py: Error: Source-side node %s not found in dictionary linked to sentence IDs!" % (s_id))
                exit(1)

            if not t_id in links_to_sentids2:
                logging.warning("sta.py: Error: Target-side node %s not found in dictionary linked to sentence IDs!" % (t_id))
                exit(1)
            cur_source = links_to_sentids1[s_id]
            cur_target = links_to_sentids2[t_id]

            if cur_source in s2t:
                if s2t[cur_source] != cur_target:
                    logging.warning("sta.py: Warning: We found a source-side node (%s), linked to a sentence ID (%s), but this node is aligned to a target-side node (%s) that is linked to a different sentence ID (%s) (different from the one to which the source-side sentence ID was already linked)." % (s_id,s2t[cur_source],t_id,cur_target))
            if cur_target in t2s:
                if t2s[cur_target] != cur_source:
                    logging.warning("sta.py: Warning: We found a target-side node (%s), linked to a sentence ID (%s), but this node is aligned to a source-side node (%s) that is linked to a different sentence ID (%s) (different from the one to which the target-side sentence ID was already linked)." % (t_id,t2s[cur_target],s_id,cur_source))

            ## Normal process: Once we have a linked sentence ID on the source side, we link it to the linked sentence ID on the target side (if it does not yet exist).
            first_time1 = 0
            first_time2 = 0
            if not cur_source in s2t:
                s2t[cur_source] = cur_target
                source_count += 1
                first_time1 = 1
            if not cur_target in t2s:
                t2s[cur_target] = cur_source
                target_count+=1
                first_time2 = 1

            if first_time1 or first_time2:
                combo = "{};{}".format(cur_source,cur_target)
                sorted_sents_combos.append(combo)

        return (source_count, target_count, sorted_sents_combos)

# logging.error("Could not find: %s in line %s\nExiting..." % (child.tail, untok_line))

    def get_x_sentences(self,tree,number):
        ## Returns the equivalent of e.g. 10 sentence pairs in the STA-XML.
        counter = 0
        to_return = []
        root=tree.getroot()
        align=tree.findall('.//align')
        for pair in align:
#            print(etree.tostring(pair))
             if self.isNextSent(pair,old_pair):
                 counter += 1
             if counter == int(number):
                 return to_return

    def isNextSent(self,pair,old_id1,old_id2):
## Unfinished
        id1 = pair[0].attrib.get("node_id")
        id2 = pair[1].attrib.get("node_id")
        return 1

class ChangeInfo:

    def replace_alignments(id,dict):
        changes_made=0
        print("> Some changes made to IDs in tree with ID %s, so we need to adapt the alignment file accordingly." %(id),file=sys.stderr)
        body = sta_tree.findall('.//alignments')[0]
        for a in sta_tree.iter("align"):
            nodes = a.findall('.//node[@treebank_id]')
            for n in nodes:
                treebank_id = n.get('treebank_id')
                if treebank_id == id:
                    if n.get('node_id'):
                        if n.get('node_id') in dict:
                            n.attrib['node_id'] = dict[n.get('node_id')]
                            changes_made=1
        return changes_made

    def sta_changeinfo(self,alignments1,alignments2):
## Given two <alignments> objects, returns a single <alignments> object consisting of all the alignments within those objects.
        new_root = etree.Element("alignments")
        for a in alignments1:
            new_root.append(a)
        for a in alignments2:
            new_root.append(a)
        return new_root
