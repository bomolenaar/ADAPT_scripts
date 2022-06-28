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

if len(sys.argv) != 4:
    raise ValueError("Please call this script with ADAPT_scoring.py [file to score] [kappa output file] [correct% output file]")

# file to score path + outfile path here
adapt_excel_path = sys.argv[1]
adapt_kappa_path = sys.argv[2]
binary_score_path = sys.argv[3]

# read the file
df = pd.read_excel(adapt_excel_path, index_col="wav_id")
df['aligned_prompt'] = df['aligned_prompt'].astype(str)
df['aligned_trans'] = df['aligned_trans'].astype(str)
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
df2 = pd.DataFrame(ls, columns=["wav_id", "word_nr", "aligned_prompt", "aligned_trans", "correctness"])
print(f"Items: {len(df2)}")

# transpose rows/cols to make rows = words
df2 = df2.transpose()
print(f"Variables: {len(df2)}")

# elicit relevant rows into vars
prompts = df2.loc["aligned_prompt"]
transcripts = df2.loc["aligned_trans"]
correctness_marks = df2.loc["correctness"]

# calculate Cohen's kappa for selected rows
print(f"Calculating kappa score for prompts and transcripts...")
k_score = kappa(prompts, transcripts)

# get nrows incorrect and calculate degree correct
correct_deg = len([c for c in correctness_marks if c == 1])/len(correctness_marks)

# write scores to output files
os.system(f"echo 'Kappa score for prompts and transcripts is {k_score}' | tee {adapt_kappa_path}")
os.system(f"echo 'Degree binary correct for prompts and transcripts is {correct_deg}' | tee {binary_score_path}")
