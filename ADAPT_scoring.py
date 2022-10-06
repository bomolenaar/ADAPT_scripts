from sklearn.metrics import cohen_kappa_score as kappa
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

if len(sys.argv) < 4:
    raise ValueError("Please call this script with ADAPT_scoring.py [ADAPT baseline] [kappa output path] [any number of ADAPT ASR outputs]")

# files to score paths + outfile path here
adapt_baseline_path = sys.argv[1]
# error_words_excel_path = adapt_excel_path.rsplit('.', 1)[0] + "_error_words.xlsx"
# error_sents_excel_path = adapt_excel_path.rsplit('.', 1)[0] + "_error_sents.xlsx"
kappas_dir = sys.argv[2]


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
        correctness = row[7]
        # if dist_score >= maxdist:
        #     outliers.append([wav_id, word_nr, aligned_prompt, aligned_trans, correctness])
        #     continue
        # else:
        ls.append([wav_id, word_nr, aligned_prompt, aligned_trans, correctness])

    # print(f'{len(outliers)} outliers @ max ADAPT edit dist {maxdist}')

    # create a new dataframe with just the rows we want (word_nr and correctness not currently used)
    df2 = pd.DataFrame(ls, columns=["wav_id", "word_nr", "aligned_ref", "aligned_hyp", "correctness"])
    print(f"Rows: {len(df2)}")

    # transpose rows/cols to make rows = words
    df2 = df2.transpose()
    print(f"Columns: {len(df2)}\n")

    return df2


def extract_words_sents(df, error_words_excel_path, error_sents_excel_path):
    # now extract only words marked as incorrect by ADAPT to investigate
    incorrect_items = df.loc[df["correct"] == 0]
    # write list to excel
    incorrect_items.to_excel(error_words_excel_path)
    print("Incorrect items:", len(incorrect_items))

    # print the % of words marked as incorrect
    deg_incor_w = len(incorrect_items)/len(df)
    print("Degree incorrect items:", deg_incor_w, '\n')

    # make a list of all sentences with at least one word marked as incorrect (present in incorrect words list)
    incorrect_list = sorted(list({wav_id for wav_id, row in incorrect_items.iterrows()}))
    incorrect_sents = pd.DataFrame(df.loc[incorrect_list])
    # write list to excel
    incorrect_sents.to_excel(error_sents_excel_path)
    print("Incorrect sentences:", len(incorrect_list))

    # print the % of sentences marked as incorrect
    deg_incor_s = len(incorrect_sents.index.unique())/len(df.index.unique())
    print("Degree incorrect sentences:", deg_incor_s, '\n')


print("Dimensions for baseline ADAPT file:")
ADAPT_base = read_adapt_table(adapt_baseline_path)
ADAPT_base_correct = ADAPT_base.loc["correctness"]

for sheetnr in range(0, len(sys.argv) - 3):
    sheet = sys.argv[3 + sheetnr]

    print(f"Dimensions for ASR ADAPT file {sheet}")
    ADAPT_AO = read_adapt_table(sheet)
    ADAPT_AO_correct = ADAPT_AO.loc["correctness"]

    ###
    # DEBUGGING snippet (keep!)

    # base_refs = zip(ADAPT_base.loc["wav_id"], ADAPT_base.loc["aligned_ref"])
    # ao_refs = zip(ADAPT_AO.loc["wav_id"], ADAPT_AO.loc["aligned_ref"])
    # allrefs = zip_longest(base_refs, ao_refs, fillvalue="?")
    # print(*list(allrefs), sep='\n')

    uniq_ids = sorted(list(set(ADAPT_base.loc["wav_id"])))
    base_id_counts = Counter(ADAPT_base.loc["wav_id"])
    ao_id_counts = Counter(ADAPT_AO.loc["wav_id"])
    differences = 0
    missing = 0
    for id in uniq_ids:
        if base_id_counts[id] != ao_id_counts[id]:
            differences += 1
            if base_id_counts[id] == 0 or ao_id_counts[id] == 0:
                missing += 1
                print(f"ID: {id}\tbase length: {base_id_counts[id]}\t ao length: {ao_id_counts[id]}\t<-- missing")
            else:
                print(f"ID: {id}\tbase length: {base_id_counts[id]}\t ao length: {ao_id_counts[id]}")
    print(f"\n{differences} differences in sentence lengths found")
    print(f"\n{missing} missing sentences found")

    # END OF DEBUGGING
    ###

    # # calculate Cohen's kappa for selected rows
    # print(f"Calculating kappa score for MT {adapt_baseline_path} and ASR output {sheet}...")
    # k_score = kappa(ADAPT_base_correct, ADAPT_AO_correct)
    # print(f"Kappa score for MT and ASR output is {k_score}")

    # # write scores to output files
    # adapt_kappa_path = os.path.join(kappas_dir, sheet.rsplit('.')[0], '.txt')
    # os.system(f"echo 'Kappa score for prompts and transcripts is {k_score}' | tee {adapt_kappa_path}")

