from sklearn.metrics import cohen_kappa_score as kappa
import pandas as pd
import sys
import os

""""
@author: Bo Molenaar
@date: 8 March 2022
@last-edited: 28 June 2022
This script takes a spreadsheet with rows = words; cols = reference, hypothesis, adapt output;
and calculates the cohen kappa score for transcription and prompt.
"""

# if len(sys.argv) != 4:
#     raise ValueError("Please call this script with ADAPT_scoring.py [file to score] [kappa output file] [correct% output file]")

# file to score path + outfile path here
adapt_excel_path = sys.argv[1]
error_words_excel_path = adapt_excel_path.rsplit('.', 1)[0] + "_error_words.xlsx"
error_sents_excel_path = adapt_excel_path.rsplit('.', 1)[0] + "_error_sents.xlsx"
# adapt_kappa_path = sys.argv[2]
# binary_score_path = sys.argv[3]

# read the file
df = pd.read_excel(adapt_excel_path, index_col="wav_id")
# df.columns[6] = df.columns[6].astype(str)
# df.columns[7] = df.columns[7].astype(str)
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
print(f"Items: {len(df2)}")

# transpose rows/cols to make rows = words
df2 = df2.transpose()
print(f"Variables: {len(df2)}\n")

# elicit relevant rows into lists
prompts = df2.loc["aligned_ref"]
transcripts = df2.loc["aligned_hyp"]
correctness_marks = df2.loc["correctness"]

# # calculate Cohen's kappa for selected rows
# print(f"Calculating global kappa score for references and hypotheses...")
# k_score = kappa(prompts, transcripts)

# # get nrows incorrect and calculate degree correct
# correct_deg = len([c for c in correctness_marks if c == 1])/len(correctness_marks)

# # write scores to output files
# os.system(f"echo 'Kappa score for prompts and transcripts is {k_score}' | tee {adapt_kappa_path}")
# os.system(f"echo 'Degree binary correct for prompts and transcripts is {correct_deg}' | tee {binary_score_path}")

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

# error_items = df.loc[df["dist_score_prompt_trans"] != 0]
# print("Error items: dist not 0")
# print(error_items)
# print()
#
# questionable = df.loc[(df["dist_score_prompt_trans"] != 0) & (df["correct"] == 1)]
# print("Questionable items: dist not 0 but correct")
# print(questionable)
# print()
