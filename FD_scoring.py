from sklearn.metrics import cohen_kappa_score as kappa
import sys
import os
import pandas as pd
import numpy as np

""""
@author: Bo Molenaar
@date: 14 June 2022
@last-edited: 
This script takes a spreadsheet with rows = words; cols = prompt, transcription, FD confidence score;
and calculates sentence, speaker and global-level confidence scores.
"""

if len(sys.argv) != 3:
    raise ValueError("Please call this script with FD_scoring.py [file to score] [output file]")

# file to score path + outfile path here
infile_path = sys.argv[1]
outfile_path = sys.argv[2]


def fix_illegal_values(score):
    if 'nan' in score:
        score = 1
    elif '-nan' in score:
        score = 0
    else:
        score = float(score)
        if score < 0:
            score = 0
        elif score > 1:
            score = 1
    return score


# read the files and get their confidence scores
def words_confs(infile):
    """
    Takes a directory with FD output, organises words and their confidence scores into lists,
    normalises erroneous FD scores and returns a global confidence score.
    :param infile: path to dir with your FD output
    :return: global confidence score (for now)
    """
    global_conf = 0
    sent_confs = []
    if infile.endswith('.xlsx'):
        df = pd.read_excel(infile, index_col="wav_id")
        words = []
        confs = []

        for wav_id, sentence, scores in df.itertuples():
            for word in sentence.split(' '):
                words.append(word)
            for score in scores.rstrip(' ').split(' '):
                confs.append(fix_illegal_values(score))

            sent_confs.append(np.mean(confs))
        global_conf = np.mean(sent_confs)

    return global_conf


conf_score = words_confs(infile_path)

os.system(f"echo 'Confidence score for prompts and audio is {conf_score}' | tee {outfile_path}")
