import sys
import pandas as pd

""""
@author: Bo Molenaar
@date: 14 June 2022
@last-edited: 
This script takes a spreadsheet with rows = sentences; cols = prompt/transcription, FD confidence score;
and outputs these into word-level pairs.
"""

if len(sys.argv) != 3:
    raise ValueError("Please call this script with FD_scoring.py [file to score] [output file]")

# file to score path + outfile path here
infile_path = sys.argv[1]
outfile_path = sys.argv[2]


def fix_illegal_values_round(score):
    if 'nan' in score:
        score = 1
    elif '-nan' in score:
        score = 0
    else:
        score = min(max(float(score), 0), 1)
    if type(score) == int:
        return score
    else:
        return float(f"{score:.3f}")


# read the files and get their confidence scores
def words_confs(infile):
    """
    Takes a directory with FD output, organises words and their confidence scores into lists,
    normalises erroneous FD scores and returns a global confidence score.
    :param infile: path to dir with your FD output
    :return: table with corrected confidence scores per word
    """
    if infile.endswith('.xlsx'):
        df = pd.read_excel(infile, index_col="wav_id")
        speaker_ids = []
        sent_ids = []
        words_ids = []
        words = []
        confs = []

        # iterate over rows and do some segmentation
        for wav_id, sentence, scores in df.itertuples():
            sent_words = sentence.rstrip(' ').split(' ')
            for word in range(len(sent_words)):
                words.append(sent_words[word])
                speaker_id, sent_id, word_id = wav_id.split('_')[0], wav_id.split('_')[2], word
                speaker_ids.append(speaker_id)
                sent_ids.append(sent_id)
                words_ids.append(word_id)
            for score in scores.rstrip(' ').split(' '):
                confs.append(fix_illegal_values_round(score))

        full_table = pd.DataFrame(
            list(zip(speaker_ids, sent_ids, words_ids, words, confs)),
            columns=["speaker", "sentence", "word_nr", "reference", "conf"]
        ).set_index("speaker")
    else:
        raise TypeError("Please provide an xlsx input file.")

    return full_table


conf_scores = words_confs(infile_path)
conf_scores.to_excel(outfile_path)

print(f"Confidence scores for prompts and audio written to {outfile_path}")
