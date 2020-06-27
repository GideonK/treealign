
# treealignery
A collection of scripts and libraries related to automated XML-based syntactic tree alignment. This repository is still under development.

## Requirements
* Python 3 (not yet tested on Python 2.x)
* lxml (https://lxml.de/installation.html) and its dependencies.

Tested on Linux Mint 18.3 Sylvia using Python 3.5.2.

## About
This software is a Python 3 reimplementation and continuation of Perl code developed by the author during his [PhD thesis](http://gideonkotze.co.za/downloads/GideonThesis_Electronic.pdf) (2013). It will also contain some Bash code. The current code has been developed in the framework of a research project supported by the Georgian National Science Foundation Grant FR-18-15744.

## Scripts

* ten-fold.py: This script creates folds for k-fold cross validation of tree alignment experiments using:
  * two parallel TIGER-XML treebank files
    * a Stockholm TreeAligner (STA) style XML alignment file referring to these treebanks.

## Libraries

* tiger.py: A list of classes and functions that handle treebank files in TIGER-XML format using lxml.etree.
* sta.py: A list of classes and functions that handle XML files in Stockholm TreeAligner format.
* files.py: File handling code.

## Data
To get started, you are welcome to download manually created Dutch/English and Dutch/French parallel treebank data, used in the author's PhD project, for your experiments:
* Dutch to English, with corrected word alignments  [.zip](http://gideonkotze.co.za/downloads/pacomt-duteng-manualword.zip)  [.tgz](http://gideonkotze.co.za/downloads/pacomt-duteng-manualword.tgz)  (140 sentence pairs)
* English to Dutch, with corrected word alignments  [.zip](http://gideonkotze.co.za/downloads/pacomt-engdut-manualword.zip)  [.tgz](http://gideonkotze.co.za/downloads/pacomt-engdut-manualword.tgz)  (150 sentence pairs)
* Dutch to French, with uncorrected word alignments  [.zip](http://gideonkotze.co.za/downloads/pacomt-dutfra-autoword.zip)  [.tgz](http://gideonkotze.co.za/downloads/pacomt-dutfra-autoword.tgz)  (158 sentence pairs)

We are planning to upload Georgian/German data as well.

We also recommend using the statistical tree alignment toolkit [Lingua-Align](https://bitbucket.org/tiedemann/lingua-align/wiki/Home) for training and testing models. Note that word alignments are an important feature for high-quality tree alignment, and that large parallel corpora are usually required to create quality word alignments. Although Lingua-Align provides some support for word alignment, there may be other word alignment solutions that may fit your needs, such as:
* [SyMGIZA++](https://github.com/emjotde/symgiza-pp)
* [fast_align](https://github.com/clab/fast_align)
* [LDC Word Aligner](https://www.ldc.upenn.edu/language-resources/tools/ldc-word-aligner)
* [efmaral](https://github.com/robertostling/efmaral)

## Related publications
Kapanadze, O., Kotzé, G. and Hanneforth, T. 2020. [Building Resources for Georgian Treebanking-based NLP](https://www.researchgate.net/publication/341821701_Building_Resources_for_Georgian_Treebanking-based_NLP) (submitted). In: _13th International Tbilisi Symposium on Language, Logic and Computation, TbiLLC 2019_, Batumi, Georgia, 16-20 September, 2019. Revised Selected Papers.

## See also
* [Stockholm TreeAligner](https://www.ling.su.se/english/nlp/tools/stockholm-treealigner): A tool providing a graphical user interface for manually aligning phrase-structure trees.
* [Lingua-Align](https://bitbucket.org/tiedemann/lingua-align/wiki/Home): A toolkit providing scripts and libraries relating to the training and testing of automated tree alignment.
* [The TIGER-XML treebank encoding format](https://www.ims.uni-stuttgart.de/documents/ressourcen/werkzeuge/tigersearch/doc/html/TigerXML.html)

Author: Gideon Kotzé
Email: dr.gideon.kotze@gmail.com
Website: www.gideonkotze.co.za
Last modified: 27 June 2020

Copyright: See LICENSE

> Written with [StackEdit](https://stackedit.io/).
