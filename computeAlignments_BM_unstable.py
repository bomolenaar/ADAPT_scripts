# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 10:40:08 2020

@author: Wieke Harmsen
@last edited: 13 June 2022 by Bo Molenaar

This script aligns the prompt (reference) and manual transcription of an audio file (hypothesis).
Each reference and hypothesis file are a separate file.
For each word in the prompt is decided whether it is correctly or incorrectly read in the audio file.

"""
import os
import glob
import sys

import adapt_graph_punct_capital_v4 as adapt_graph
import re
import pandas as pd
from multiprocessing import Pool

# to read
path_to_xlsx_folder = sys.argv[1]
path_to_prompt_trans = path_to_xlsx_folder + '/tables/' + sys.argv[2]

# to write
path_to_adapt = path_to_xlsx_folder + '/adapt/' + sys.argv[3]


def main():

    mypool = Pool()

    ref_name_list, ref_trans_list = readReferenceFiles(path_to_prompt_trans)
    hyp_name_list, hyp_trans_list = readHypothesisFiles(path_to_prompt_trans)

    #Preprocessing of transcriptions
    ref_trans_list = replace_spaces(ref_trans_list)
    hyp_trans_list = replace_spaces(hyp_trans_list)
    
    #Match hypothesis and reference transcription
    #Structure: name - ref - ref reversed - hyp - hyp reversed

    # FIXME
    #  this is all fucked up
    args = zip(ref_name_list, ref_trans_list, hyp_name_list, hyp_trans_list)
    data = mypool.starmap(match_ref_hyp, list(args))
    # print(data)
    
    #Align the reversed ref and reversed hyp
    data_with_alignments = use_ADAPT_graph(data)
    
#    #Save matrix as dataframe and write dataframe to csv
#    df_align = pd.DataFrame(data_with_alignments, columns = ["id", 'prompt', 'trans'])
#    df_align.to_csv(path_to_alignment, index = False)
#    print("csv alignments file made")
    
    #Convert format of data to word list
    data_as_wordlist = change_format_to_wordlist(data_with_alignments)
#    print("data as wordlist: ",data_as_wordlist) #uncomment
   
    # read comparison file
    df = pd.read_excel(path_to_prompt_trans)
    
    #Save word list matrix as dataframe and write to csv
    data_as_wordlist_new = []
    adapt_score_lst = []
    merge_lst = []
    for i in data_as_wordlist:
        id_name = i[0]
        word_idx = i[1] + 1
        word_nr = i[1]
        aligned_1 = i[2]
        aligned_2 = i[3]
        align_correct = i[4]
        check_recommended = i[5]
        
        data_as_wordlist_new.append(i)
        
        align = compute_alignments([i[2]], [i[3]])
        [new_align] = align
        dist_score = new_align[0]
        nr_of_sub = new_align[1]
        nr_of_del = new_align[2]
        nr_of_ins = new_align[3]
        
        adapt_score_lst.append([id_name] + new_align[:-2] + i[1:])
#        print(new_align)

#    print(data_as_wordlist)
#    print(adapt_score_lst)

#    df_words = pd.DataFrame(data_as_wordlist_new, columns = ["name", "word_nr", "aligned_1", "aligned_2", "correct", "check_recommended"])
#    df_words.to_csv(prompt_jasmin_asr_word_correct, index = False)
#    print("csv word correct file made")
    
    dist_column_name = "dist_score" + "_" + 'ref' + "_" + 'hyp'
    aligned_1 = "aligned_" + 'ref'
    aligned_2 = "aligned_" + 'hyp'
    df_adapt_score = pd.DataFrame(adapt_score_lst, columns = ["wav_id",dist_column_name,"nr_of_sub","nr_of_del","nr_of_ins", "word_nr", aligned_1, aligned_2, "correct", "check_recommended"])
    df_adapt_score.to_excel(path_to_adapt, index = False)
    print("xlsx adapt score file between reference and hypothesis made!")
    print(df_adapt_score.shape)
    
#    df_adapt_score_sub = df_adapt_score[['id', dist_column_name]]
#    print(df_adapt_score_sub)
#    df_merge = pd.merge(df, df_adapt_score_sub)
#    df_merge.to_csv(path_to_merge_df, index=False)
#    print('merge df done!')


def readReferenceFiles(xlsx):
    """
    This function extracts for every reference file (=prompt) in the directory two things:
        - the name of the file
        - the prompt transcription
    """

    df = pd.read_excel(xlsx)
    if "_MT." in xlsx:
        ref_list = df['Manual transcription'].to_list()
    elif "_PR." in xlsx:
        ref_list = df['Prompt'].to_list()
    else:  # ugly but works for now, expect bugs
        ref_list = df['Prompt'].to_list()
    name_list = df['wav_id'].to_list()
        
    return name_list,ref_list


#"""
#Some TextGrid files start with the line: 3 File type = "ooTextFile"
#This function removes the initial "3".
#This is necessary to use the TextGrids package.
#"""
#def change_format_first_line(file_name):
#    with open(file_name) as f:
#            lines = f.readlines()
#            first_line = lines[0]
#            if(first_line.find("3 ") != -1):
#                new_first_line = first_line.replace("3 ", "")
#                lines[0] = new_first_line
#                
#                with open(file_name, "w") as f:
#                    f.writelines(lines)


def readHypothesisFiles(xlsx):
    """
    This function extracts for every hypothesis file (=manual transcription of the audio file) in the directory two things:
        - the name of the file
        - the manual transcription
    """

    df = pd.read_excel(xlsx)
    if ("_MT" in xlsx) or ("_PR" in xlsx):
        hyp_list = df['ASR output'].to_list()
    else:
        hyp_list = df['Manual transcription'].to_list()
    name_list = df['wav_id'].to_list()
        
    return name_list,hyp_list


def replace_spaces(trans_list):
    """
    Replace each space with a pipe (= | ), such that the strings can be used as input to the ADAPT algorithm.
    """

    new_list = []
    for t in trans_list:
        if isinstance(t, float):
            t = 'nan'
        else:
            t = t.replace(" ", "|")
        new_list.append(t)
    return new_list


def reverse(s):
    """
    Function that reverses a given string.
    """

    str = "" 
    for i in s: 
      str = i + str
    return str


def match_ref_hyp(ref_name, ref_trans, hyp_name, hyp_trans):
    """
    This function creates a matrix in which the references and hypotheses with the same file name are matched.
    It also adds two extra columns, one with the reversed reference and one with the reversed hypothesis.
    """

    data = []
    sample = []

    name = ref_name[i]
    sample.append(name)

    ref = ref_trans[i]
    sample.append(ref)
    sample.append(reverse(ref))

    hyp_idx = hyp_name.index(name)
    hyp = hyp_trans[hyp_idx]
    sample.append(hyp)
    sample.append(reverse(hyp))

    data.append(sample)
    return data
        

def use_ADAPT_graph(data):
    """
    This function aligns the reversed reference and the reversed hypothesis using a python version of ADAPT.
    """

    aligned_data = []
    count = 0
    
    for sample in data:
        # print('sample: ',sample)
        print("processing: ", count)
        count += 1
        
        aligned_sample = []
        
        rev_ref = sample[2].lower()
        rev_hyp = sample[4].lower()
        
#        print("rev_ref: \n", rev_ref)
#        print("rev_hyp: \n", rev_hyp)

        dist_score, nsub, ndel, nins, align_rev_ref, align_rev_hyp = adapt_graph.align_dist(rev_ref, rev_hyp)
        
#        print("aligned ref reversed: \n", align_rev_ref)
#        print("aligned hyp reversed: \n",align_rev_hyp)
        
        align_ref = reverse(align_rev_ref)
        align_hyp = reverse(align_rev_hyp)
        
#        print("aligned ref: \n", reverse(align_rev_ref))
#        print("aligned hyp: \n", reverse(align_rev_hyp))
        
        begin = 0
        selection_list = []
        
        #Search indices of -----| parts
        while re.search("\-+\|", align_ref[begin:]) != None:
            selection = []
            start_span = re.search("\-+\|", align_ref[begin:]).span()[0] +begin
            end_span = re.search("\-+\|", align_ref[begin:]).span()[1] +begin
            selection.append(start_span)
            selection.append(end_span)
            selection_list.append(selection)
            begin = end_span
        
        #Switch first - and last | in selection list, such that missing words are represented correctly
        for sel in selection_list:
            align_ref = align_ref[:sel[0]] + "|" + align_ref[sel[0] + 1:]
            align_ref = align_ref[:sel[1]-1] + "-" + align_ref[sel[1]:]
            
        #print("end ref: \n", align_ref)
        #print("end hyp: \n", align_hyp)    
            
        aligned_data.append([sample[0], align_ref, align_hyp])
    return aligned_data
        

def change_format_to_wordlist(data_with_alignments):
    """
    This function converts the format of the data from a "sentence" to a "word list"
    """

    word_list = []
    for sample in data_with_alignments:
#        print(sample)
        name = sample[0]
        if '|' not in sample[1]:
            align_ref = sample[1] + '|' #for one word
        else:
            align_ref = sample[1]
        align_hyp = sample[2]
    
        start_idx = 0
        end_idx = 0
        r_list = []
        h_list = []
        
        ## Align hyp contains no word boundaries
        if align_hyp.find("|") == -1:
            while align_ref.find("|", start_idx) != -1:
                first_wbn = align_ref.index("|", start_idx)
                r_list.append(align_ref[start_idx:first_wbn])
                h_list.append(align_hyp[start_idx:first_wbn])
                start_idx = first_wbn+1

        ## Align hyp contains word boundaries
        else: 
            for i in range(len(align_ref)):
                
                if align_ref[i] == "|" :
                    
                    end_idx = i
                    
                    #First word in ref
                    if start_idx == 0:
                        r_list.append(align_ref[start_idx:end_idx])
                        h_list.append(align_hyp[start_idx:end_idx])
                        
                    #Middle word in ref
                    elif start_idx != 0: 
                        r_list.append(align_ref[start_idx+1:end_idx])
                        h_list.append(align_hyp[start_idx+1:end_idx]) 

                    #last word in ref
                    if(align_ref.find("|", end_idx+1) == -1):
                        r_list.append(align_ref[end_idx+1:].replace("|", ""))
                        h_list.append(align_hyp[end_idx+1:])
                    
                    start_idx = end_idx
                
         
#        print("lists:")
#        print(r_list)
#        print(h_list)
        
        for i in range(len(r_list)):
            row = [] 
            row.append(name)
            row.append(i)
            row.append(r_list[i])
            row.append(h_list[i])
            
            #Check whether last attempt is correct
            if h_list[i].find(r_list[i].replace("-", "")) != -1:
                row.append(1)
            else:
                row.append(0)
            
            #Contains ----?
            if re.search("\-{2,}", r_list[i]) != None:
                row.append(1)
            else:
                row.append(0)
            
            #print("row\n", row)
   
            word_list.append(row)
            
    return word_list
       

def compute_alignments(ref, hyp):
    
    assert len(ref) == len(hyp), "The number of references and hypotheses is not equal."
    
    align = []
    for i in range(len(ref)):
        
        #compute alignments + nr of operations
        dist_score, nsub, ndel, nins, align_ref, align_hyp = adapt_graph.align_dist(ref[i], hyp[i])
        
        #save alignments + nr of operations as list
        output_align_algorithm = [dist_score, nsub, ndel, nins, align_ref, align_hyp]
        align.append(output_align_algorithm)
    
    return align



main()
