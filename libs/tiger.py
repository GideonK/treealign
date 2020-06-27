#!/usr/bin/python3

import re, sys, os
from lxml import etree
import sta, data

# class Elements:
#     def __init__(self,tree):
#         self.root = tree.getroot()

class GetInfo:
    def get_sent_ids(self,tree):
        root=tree.getroot()
#        sents = tree.findall('.//s')
        ids=[]
        for element in root.iter("s"):
            ids.append(element.attrib['id'])
        return ids

    def get_sentid(self,node_id):
## Receives a node id in the following format, e.g.
## s158_506
## and extracts the sentence ID, e.g. s158
        return re.findall('(.*?[0-9]+)_?', node_id)[0]

    def get_current_sentid(self,sent_el):
## Receives a tree object describing a TIGER-XML sentence
## Returns, in the form of a list, all sentence IDs that were detected.
        pass

    def get_unique_sentids_in_sent(self,treesent):
## Given a sentence (<s>) in a TIGER-XML, return the number of unique sentence IDs - normally expected to be only 1 - in the sentence.
        sentid=treesent.attrib['id']
        ids = {}
        ids[sentid] = 1
        for t in treesent.iter("t"):
            t_id = self.get_sentid(t.attrib['id'])
            if not t_id in ids:
                ids[t_id] = 1
        for nt in treesent.iter("nt"):
            nt_id = self.get_sentid(nt.attrib['id'])
            if not nt_id in ids:
                ids[nt_id] = 1
        for edge in treesent.iter("edge"):
            edge_id = self.get_sentid(edge.attrib['idref'])
            if not edge_id in ids:
                ids[edge_id] = 1

        return len(ids)

    def get_nr_sents(self, tree, also_check_other_nodes):
# (nr_sents, nr_uniq, non_uniq_ids, sents_with_two_or_more) = tiger_getinfo.get_nr_sents(stree,1)
## - Get the number of sentences as represented by IDs under <s> elements
## - Also get the number of unique IDs
## - If they differ, return the IDs that are not unique
## - also_check_other_nodes: also check <t>, <nt> and <edge> nodes for unique IDs
        non_uniq = []
        sents_with_two_or_more = []
        id_dict = {}
        nr_sents = 0
        nr_non_uniq = 0
        root = tree.getroot()
        for s in root.iter("s"):
            nr_sents += 1
            id = s.attrib['id']
            if id in id_dict:
                non_uniq.append(id)
                nr_non_uniq += 1
            else:
                id_dict[id] = 1
            if also_check_other_nodes:
                unique_ids = self.get_unique_sentids_in_sent(s)
                if unique_ids > 1:
                    sents_with_two_or_more.append(id)
#                    print("More than one unique id ("+str(unique_ids)+") for sentence: "+str(id)+"!")

        if nr_non_uniq > 0:
            nr_uniq = nr_sents-nr_non_uniq
        else:
            nr_uniq = nr_sents

        return (nr_sents,nr_uniq,non_uniq,sents_with_two_or_more)

    def any_sentids_have_leading_zeros(self,tree):
        root = tree.getroot()
        has_leading_zero = 0
        leading_zeros = []
        for s in root.iter("s"):
            id = s.attrib['id']
            if bool(re.match('^s?0+[0-9]+', id)):
                has_leading_zero = 1
                leading_zeros.append(id)
        return (has_leading_zero,leading_zeros)

    def link_nodes_to_sentids(self,tree):
## Returns a dictionary, linking each alignable node in a given treebank to its sentence ID. In this way, we can count the real number of sentences represented even if some sentences in the treebank can consist of nodes referring to more than one sentence ID.
        linked_nodes = {}
        root = tree.getroot()
        for s in root.iter("s"):
            sentid=s.attrib['id']
            for t in s.iter("t"):
                t_id = t.attrib['id']
                linked_nodes[t_id] = sentid
            for nt in s.iter("nt"):
                nt_id = nt.attrib['id']
                linked_nodes[nt_id] = sentid

        return linked_nodes

    ## Returns a list of all <t> and <nt> nodes (attribute "id") values in the tree object
    ## Returns either as a list or dictionary
    def get_nodes(self,tree,data_type):
        root = tree.getroot()
        if data_type == "dict":
            nodes={}
        elif data_type == "list":
            nodes=[]
        else:
            nodes={}
            return nodes
        for element in root.iter("t"):
            if data_type == "list":
                nodes.append(element.attrib['id'])
            elif data_type == "dict":
                nodes[element.attrib['id']] = "t"
        for element in root.iter("nt"):
            if data_type == "list":
                nodes.append(element.attrib['id'])
            elif data_type == "dict":
                nodes[element.attrib['id']] = "nt"
        return nodes

    def get_words(self,tree):
        words = {}
        for element in tree.iter("t"):
            id = element.attrib['id']
            word = element.attrib['word']
            words[id] = word
        return words

    def get_sent_words(self,sent_tree):
        sent = ""
        for t in sent_tree.iter("t"):
            sent = sent+t.attrib['word']+" "
        return sent.rstrip()

    def getnodesentid(self,node_el):
## E.g. (nodeid,sentid) = tiger_getinfo.getnodesentid(t)
## Given a <t>, <nt> or <idref> element, extract the sentence ID (before the underscore, e.g. "3" in "s3_44") and the node ID (after the underscore, e.g. "44" in "s3_44")
        id = node_el.get("id")
        if bool(re.match('s?[0-9]+_[0-9]+', id)):
            nodeid = re.findall('_([0-9]+)', id)[0]
            sentid = re.findall('([0-9]+)_', id)[0]
        else:
            print("ERROR: Node ID is malformed ("+id+")! It is supposed to consists of a number, followed by an underscore, followed by another number (e.g. \"s3_44\").", file=sys.stderr)
            sys.exit(1)

        return (nodeid, sentid)

    def nodesarevalid(self,el):
## Given a tree, test if idref IDs refer to IDs that exist in the tree.
## Returns 1 and an empty list if all are valid, otherwise returns 0 and a list of IDs that do not exist
        invalidnodes = []
        sents = el.findall('.//s[@id]')
        for s in sents:
            node_exists = {}
            idrefs = []
            terminals = s.findall('.//t[@id]')
            nonterminals = s.findall('.//nt[@id]')
            for t in terminals:
                id = t.get("id")
                node_exists[id] = 1
            for nt in nonterminals:
                id = nt.get("id")
                node_exists[id] = 1
                for edge in nt:
                    id = edge.get("idref")
                    idrefs.append(id)

            for id in idrefs:
                if id in node_exists:
                    pass
                else:
                    invalidnodes.append(id)

        return (invalidnodes)

    def build_nonterm_links(self,nonterminals):
        nlinks = {}
        for n in nonterminals:
            ntid = n.get('id')
            for child in n:
                if child.tag == "edge":
                    nlinks.setdefault(ntid, []).append(child.get('idref'))
        return nlinks

    def return_firstlevel_nodes(self,sent):
    ## Given an lxml.etree element representing a TIGER-XML tree of a sentence (<s>), returns a list of <nt> elements that only have terminal nodes as children.
        pass

class ChangeInfo:

    def unify_sentids(self,el,sentlist):
        ## e.g. new_sents = unify_sentids(body,sents_with_two_or_more) ## in tiger.py
        ## el: lxml.etree element, e.g. a <body>
        ## sentlist: a list of string values, each corresponding to the value of an "id" attribute within an <s> element
        ## ==> Can be extracted using def get_nr_sents under class GetInfo in this file.
        ## ==> sentlist refers to TIGER-XML trees where not all the ID values under <t>, <nt> and <edge> refer to the same sentence ID under <s>. This def unifies them, making them all the same, and in a way that links are not broken.
        ## checks where nodes within the <s> structure have IDs that do not correspond to the ID of the <s>, e.g.
        ## <s id="s83"> ... <t id="s83_4"> ==> corresponds
        ## <s id="s83"> ... <t id="s830_4"> ==> does not correspond
        ## Returns:
        ## - Changed <s> element (with e.g. id="s83_5" instead of id="s830_4" and resulting idref changes)
        ## - List of all changes so that alignment file (optionally) can also be changed
        ## Any 0s before ID numbers are removed to have a consistent list of IDs.
        data_dicts = data.Dicts()

        orignew = {}
        neworig = {}
        s_exists = {}
        t_exists = {}
        nt_exists = {}
        tiger_getinfo = GetInfo()
        tree = etree.ElementTree(el)

        for i in sentlist:
            s_exists[i] = 1

        sents = el.findall('.//s[@id]')
        for s in sents:
            change_tid = []
            change_ntid = []
            if s.get("id") in s_exists:
                ssentid = s.get("id") ## e.g. "s103_5"
                pat = re.compile(r'^s?(.+)$')
                sentid = re.findall(pat, ssentid)[0] ## e.g. "103_5"
                tmax = 1
                ntmax = 500
                terminals = s.findall('.//t[@id]')
                ## We need to keep track of the nodes to which the nonterminals link.
                ## First we go through all <t> and make a list of all the IDs.
                ## IDs that do not correspond to the sentence ID (see above example) are marked to be changed.
                ## By default, the change will be one number higher than the previous legitimate number, e.g.
                ## <s id="s83">
                ## ...<t id="s83_4"> ==> corresponds
                ## ...<t id="s830_1"> ==> does not correspond, so we change it to id="s83_5">
                ## unless that number has already been taken, in which case we change it to the next higher number that has not been taken, i.e. s83_6, etc.
                ## Each change is recorded in two dictionaries:
                ## - orignew: key/value pair: original ID => new ID, e.g. s830_1 ==> s83_5
                ## - neworig: key/value pair: new ID => original ID, e.g. s83_5 ==> s830_1
                ## We do the same for non-terminals.
                ## When iterating through idref values within non-terminals (the nodes to which they refer), this needs to happen in two steps:
                ## - Since both the non-terminal ID and the idref ID may have changed, we need to consult both dictionaries to make the right connections. For example:
                ## - <nt id="s830_500"> was changed to <nt id="s83_505">. So we need to determine that the original ID was s830_500, and which nodes it referred to (which may also have changed).
                ## -- neworig: get the original ID for <nt>, e.g. we use this to determine that s83_505 was originally s830_500.
                ## -- orignew: get the new IDs for the old idref values listed in neworig, e.g. we use this to determine which nodes the original s830_500 dominated.
                ## neworig and orignew must be passed back since it can be used to change the corresponding IDs in an alignment file.
                must_change = 0
                has_changed = 0
                for t in terminals:
                    (nodeid,t_sentid) = tiger_getinfo.getnodesentid(t) ## e.g. in "s103_12", it returns "12" and "103"
                    t_id = t.get("id")
                    t_exists[t_id] = 1
                    if (t_sentid != sentid) or re.search(r'^0',nodeid):
                   ## i.e. If the sentence ID extracted from the current terminal node is different from that displayed in <s>, or the terminal node ID starts with 0 (we want to be consistent and not have any IDs start with 0). This will be changed after the for loop.
                        change_tid.append(tree.getelementpath(t)) ## We append the XPath of the terminal node to be changed to a list for later processing. We then use the same XPath later on to retrieve the correct element.
                        must_change = 1
                        has_changed = 1
                    else: ## nothing wrong, the terminal has the correct sentence ID and does not start with 0
                        if int(nodeid) > tmax:
                           tmax = int(nodeid)
                if must_change == 1:
                    for t in change_tid: ## We traverse the list of XPaths and process each terminal node that needs to be changed.
                        change_t = tree.xpath(t)[0] ## the <t> element
                        t_id = change_t.get("id") ## its ID
                        if t_id in neworig: ## Here, we check if it has already been changed. If so, we do nothing.
                            has_changed = 0
                        else:
                            new_t = tmax + 1
                            new_id = "s"+sentid+"_"+str(tmax)
                            if new_id in t_exists:
                               while new_id in t_exists:
                                    tmax = tmax + 1
                                    new_id = "s"+sentid+"_"+str(tmax)
                            else:
                                tmax = tmax + 1

                            t_exists[new_id] = 1
                            change_t.attrib['id'] = new_id
                            orignew[t_id] = new_id
                            neworig[new_id] = t_id
                must_change = 0
                nonterminals = s.findall('.//nt[@id]')

                nlinks = tiger_getinfo.build_nonterm_links(nonterminals) ## We store each idref ID that is associated with a specific non-terminal

                for nt in nonterminals:
                    (nodeid,nt_sentid) = tiger_getinfo.getnodesentid(nt)
                    nt_id = nt.get("id")
                    nt_exists[nt_id] = 1
                    if (nt_sentid != sentid) or re.search(r'^0',nodeid):
                        must_change = 1
                        has_changed = 1
                        change_ntid.append(tree.getelementpath(nt))
                    else:
                        if int(nodeid) > ntmax:
                            ntmax = int(nodeid)
                if must_change == 1:
                    for nt in change_ntid: ## we go through a list of IDs that we need to change. Each "nt" is an XPath.
                        change_nt = tree.xpath(nt)[0] ## takes the XPath, uses it to search for the corresponding element in the tree and returns it.
                        nt_id = change_nt.get("id") ## This is the NT corresponding to the XPath. Note that it may have changed in the meantime.
                        if nt_id in neworig:
                            has_changed = 0
                        else:
                            new_nt = ntmax + 1
                            new_id = "s"+sentid+"_"+str(ntmax)
                            if new_id in nt_exists:
                                while new_id in nt_exists:
                                    ntmax = ntmax + 1
                                    new_id = "s"+sentid+"_"+str(ntmax)
                            else:
                                ntmax = ntmax + 1
                            nt_exists[new_id] = 1
                            change_nt.attrib['id'] = new_id
                            orignew[nt_id] = new_id
                            neworig[new_id] = nt_id
                if has_changed == 1: ## meaning that we need to change idref values as well
                    # for k in nlinks: ## each of the non-terminal IDs that has idref IDs associated with it.
                    # ## Some of them may have changed, so we check for this first.
                    for nt in nonterminals:
                        nt_id = nt.get("id")
                        if nt_id in neworig: ## We check if the current ID has been changed (i.e. not in the original tree). If so, it has already been changed in the tree object, so we check in the neworig dictionary for the old value. We need the old value because the links we built earlier with build_nonterm_links have been built with the old ID values. We use these values to retrieve all idref IDs underneath each non-terminal ID (under <edge>) from the previously built nlinks dictionary.
                            nlinks_key = neworig[nt_id]
                        else:
                            nlinks_key = nt_id
                        edges = nt.findall('.//edge[@idref]')
                        for e in edges:
                            e_id = e.get("idref")
                            if e_id in data_dicts.get_values_if_any(nlinks, nlinks_key):
                                ## i.e. if the current idref is associated with the current NT ID (or old NT ID, if it has changed)
                                ## We still need to check if the current idref has changed.
                                if e_id in orignew:
                                    e.attrib['idref'] = orignew[e_id]
                            else:
                                ## i.e. if the current idref is NOT associated with the current NT ID (or the old NT ID, if it has changed)
                                ## Check if the idref has been changed as well.
                                if e_id in orignew:
                                    ## e_id is old and has a new value, we should change it.
                                    e.attrib['idref'] = orignew[e_id]
                                else:
                                    print("Edge id:",e_id,file=sys.stderr)
                                    print("  It is not associated with the current NT ID (possibly old version of new changed one):",nlinks_key,file=sys.stderr)
                                    if e_id in orignew:
                                        print ("Edge ID has changed. It is in orignew.",file=sys.stderr)
                                    else:
                                        print ("Edge ID have not changed. It is not in orignew.",file=sys.stderr)
#                print(etree.tostring(s, pretty_print=True, encoding="unicode"))
        return orignew

    def change_all_sentids(self,tree,start_at,leading_zeros):
    ## Given a TIGER-XML tree, change all sentence IDs (part before "_") of all nodes with leading zeros (list "leading_zeros") starting at a given value (e.g. 2000).
    ## Example: orignew = tiger_changeinfo.change_all_sentids(tree[id],normalize_ids_from,leading_zeros)
        cur_num = start_at
        cur_id = "s"+str(cur_num)
        orignew = {}
        sents = tree.findall('.//s[@id]')
        for s in sents:
            id = s.get('id')
            if id in leading_zeros:
                s.attrib['id'] = cur_id
                graph = s.findall('.//graph[@root]')[0]
                graph.attrib['root'] = cur_id
                terminals = s.findall('.//t[@id]')
                for t in terminals:
                    id = t.get('id')
                    if re.search('s?0+[0-9]+_',id):
                        new_id = re.sub("s?0+[0-9]+(_)",cur_id+"\\1",id)
                        t.attrib['id'] = new_id
                        orignew[id] = new_id
                nonterms = s.findall('.//nt[@id]')
                for nt in nonterms:
                    id = nt.get('id')
                    if re.search('s?0+[0-9]+_',id):
                        new_id = re.sub("s?0+[0-9]+(_)",cur_id+"\\1",id)
                        nt.attrib['id'] = new_id
                        orignew[id] = new_id
                    edges = nt.findall('.//edge[@idref]')
                    for e in edges:
                        idref = e.get('idref')
                        if re.search('s?0+[0-9]+_',idref):
                            new_id = re.sub("s?0+[0-9]+(_)",cur_id+"\\1",idref)
                            e.attrib['idref'] = new_id
                cur_num = int(cur_num)+1
                cur_id = "s"+str(cur_num)
        return orignew
