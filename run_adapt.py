# -*- coding: utf-8 -*-
"""
Run this file to use the ADAPT algorithm.
This file is the Python version of the Perl file run_adapt.pl

@author: Wieke Harmsen
@date created: 7 September 2020
@data last adaptations: 7 september 2020

edited by Bo Molenaar 17-2-2022 to take sys args -> allows call with required files as args
and                   24-2-2022 to use adapt_grapg_punct_capital_v4
"""

#Import the right file:
# adapt_phone.py for phoneme-phoneme alignment
# adapt_graph.py for grapheme-grapheme alignment (using levenshtein)
import adapt_graph_punct_capital_v4 as adapt
import sys

if len(sys.argv) != 4:
    raise ValueError("Please call this script with run_adapt.py [reference_file] [hypothesis_file] [output_file]")

#specify these three variables before running the script:
ref_file = sys.argv[1]
hyp_file = sys.argv[2]
output_file = sys.argv[3]

def main():
    
    #read files
    ref = read_and_preprocess_file(ref_file)
    hyp = read_and_preprocess_file(hyp_file)
    
    #compute alignments
    alignments = compute_alignments(ref, hyp)
    
    #write alignments to output file
    write_output(alignments)
    

def read_and_preprocess_file(file):
    
    with open(file) as f:
        
        #read lines in file
        lines = f.readlines()
        
        #remove new lines
        for i in range(len(lines)):
            lines[i] = lines[i].replace("\n", "")
        
    return lines
        

def compute_alignments(ref, hyp):
    
    assert len(ref) == len(hyp), "The number of references and hypotheses is not equal."
    
    align = []
    for i in range(len(ref)):
        
        #compute alignments + nr of operations
        dist_score, nsub, ndel, nins, align_ref, align_hyp = adapt.align_dist(ref[i], hyp[i])
        
        #save alignments + nr of operations as list
        output_align_algorithm = [dist_score, nsub, ndel, nins, align_ref, align_hyp]
        align.append(output_align_algorithm)
    
    return align

def write_output(align):
    
    #write the alignments and nr of operations to txt file
    with open(output_file, "w") as f:
        f.write("Reference;Hypothesis;Dist_score;Nr_of_sub;Nr_of_del;Nr_of_ins\n")
        for row in align:
            f.write(row[4] + ";" +row[5] + ";" +str(row[0]) + ";" + str(row[1]) + ";" + str(row[2]) + ";" + str(row[3]) + "\n")

main()