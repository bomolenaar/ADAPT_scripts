import pandas as pd
import sys
import os
from itertools import zip_longest
from collections import Counter

""""
@author: Bo Molenaar
@date: 8 March 2022
@last-edited: 28 June 2022
This script takes a set of ADAPT output spreadsheets: 1 baseline Prompt-MT and any number of ASR output-MT
and calculates the cohen kappa score for agreement between the baseline and each ASR output.
"""

if len(sys.argv) not in {2, 3, 4}:
    raise ValueError("Please call this script with ADAPT_scoring.py [ADAPT baseline] [optional error words output] [optional error sentences output]")

# ADAPT baseline file path
adapt_baseline_path = sys.argv[1]
if len(sys.argv) == 4:
    words_out = sys.argv[2]
    sents_out = sys.argv[3]


def read_adapt_table(adapt_path):
    # read the file
    df = pd.read_excel(adapt_path, index_col="wav_id")
    ls = []
    # outliers = []
    # maxdist = 10

    # elicit the rows we want into a list
    for wav_id, row in df.iterrows():
        dist_score = row[0]
        nr_sub = row[1]
        nr_del = row[2]
        nr_ins = row[3]
        word_nr = row[4]
        aligned_prompt = row[5]
        aligned_trans = row[6]
        correct = row[7]
        # if dist_score >= maxdist:
        #     outliers.append([wav_id, word_nr, aligned_prompt, aligned_trans, correctness])
        #     continue
        # else:
        ls.append([wav_id, dist_score, nr_sub, nr_del, nr_ins, word_nr, aligned_prompt, aligned_trans, correct])

    # print(f'{len(outliers)} outliers @ max ADAPT edit dist {maxdist}')

    # create a new dataframe with just the rows we want (word_nr and correctness not currently used)
    df2 = pd.DataFrame(ls, columns=["wav_id", "dist_score", "nr_sub", "nr_del", "nr_ins", "word_nr", "aligned_ref", "aligned_hyp", "correct"]).set_index("wav_id")
    print(f"Rows: {len(df2)}")

    print(f"Columns: {df2.shape[1]}\n")

    return df2


def extract_words_sents(df, error_words_excel_path=None, error_sents_excel_path=None):
    # now extract only words marked as incorrect by ADAPT to investigate
    incorrect_items = df.loc[df["correct"] == 0]
    print("Incorrect items:", len(incorrect_items))

    # print the % of words marked as incorrect
    deg_incor_w = len(incorrect_items)/len(df)
    print("Degree incorrect items:", deg_incor_w, '\n')

    # print the mean and sd for ADAPT distance score per word
    adapt_mean_incor_w = incorrect_items['dist_score'].mean()
    adapt_sd_incor_w = incorrect_items['dist_score'].std()
    print("Mean ADAPT distance score for incorrect items:", adapt_mean_incor_w)
    print("SD of ADAPT distance score for incorrect items:", adapt_sd_incor_w, '\n')

    # make a list of all sentences with at least one word marked as incorrect (present in incorrect words list)
    incorrect_list = sorted(list({wav_id for wav_id, row in incorrect_items.iterrows()}))
    incorrect_sents = pd.DataFrame(df.loc[incorrect_list])
    n_incorrect_sents = set(incorrect_sents.index)
    print("Incorrect sentences:", len(n_incorrect_sents))

    # print the % of sentences marked as incorrect
    deg_incor_s = len(incorrect_sents.index.unique())/len(df.index.unique())
    print("Degree incorrect sentences:", deg_incor_s, '\n')

    # print the mean and sd for ADAPT distance score per sentence
    adapt_mean_incor_s = incorrect_sents.groupby('wav_id')['dist_score'].sum().mean()
    adapt_sd_incor_s = incorrect_sents.groupby('wav_id')['dist_score'].sum().std()
    print("Mean ADAPT distance score for incorrect sentences:", adapt_mean_incor_s)
    print("SD of ADAPT distance score for incorrect sentences:", adapt_sd_incor_s, '\n')

    if error_words_excel_path:
        # write list to excel
        incorrect_items.to_excel(error_words_excel_path)
    if error_sents_excel_path:
        # write list to excel
        incorrect_sents.to_excel(error_sents_excel_path)


print("Dimensions for baseline ADAPT file:")
ADAPT_base = read_adapt_table(adapt_baseline_path)
extract_words_sents(ADAPT_base)

# for sheetnr in range(0, len(sys.argv) - 3):
#     sheet = sys.argv[3 + sheetnr]
#
#     print(f"Dimensions for ASR ADAPT file {sheet}")
#     ADAPT_AO = read_adapt_table(sheet)
#     ADAPT_AO_correct = ADAPT_AO.loc["correctness"]
#
#     ###
#     # DEBUGGING snippet (keep!)
#
#     # uniq_ids = sorted(list(set(ADAPT_base.loc["wav_id"])))
#     # base_id_counts = Counter(ADAPT_base.loc["wav_id"])
#     # ao_id_counts = Counter(ADAPT_AO.loc["wav_id"])
#     # differences = 0
#     # missing = 0
#     # for id in uniq_ids:
#     #     if base_id_counts[id] != ao_id_counts[id]:
#     #         differences += 1
#     #         if base_id_counts[id] == 0 or ao_id_counts[id] == 0:
#     #             missing += 1
#     #             print(f"ID: {id}\tbase length: {base_id_counts[id]}\t ao length: {ao_id_counts[id]}\t<-- missing")
#     #         else:
#     #             print(f"ID: {id}\tbase length: {base_id_counts[id]}\t ao length: {ao_id_counts[id]}")
#     # print(f"{differences} differences in sentence lengths found")
#     # print(f"{missing} missing sentences found\n")
#
#     # END OF DEBUGGING
#     ###

