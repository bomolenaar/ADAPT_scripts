import csv
from pathlib import Path
import os
import re
import pandas as pd
import sys
import argparse

""""
@Author: Bai Yu
@Author: Bo Molenaar
@Date: 14 June 2022

This script takes 2 directories of files, either orthographic transcriptions, prompts, ASR output or forced decoding
results, and creates a table with the utterance ID and specified hypothesis and reference for that ID.
There are different types of tables possible, i.e. different hyp/ref pairs, namely:
. MT_PR (ort. trans : prompt);
. AO_MT (ASR output : ort. trans);
. AO_PR (ASR output : prompt);
. FD (Forced Decoding results)
"""

parser = argparse.ArgumentParser()
# type of table to make. options:
# . MT_PR
# . AO_MT
# . AO_PR
# . FD
parser.add_argument("table_type", choices=["MT_PR", "AO_MT", "AO_PR", "FD"],
                    help="Specify the hypothesis and reference type.\n"
                         "FD = Forced Decoding, MT = Manual Transcriptions, AO = ASR Output\n"
                         "Options: MT_PR, AO_MT, AO_PR, FD")
parser.add_argument("hypotheses_path", help="Path to hypotheses to compare")
if "FD" not in sys.argv[1]:
    parser.add_argument("references_path", help="Path to references to compare against")
parser.add_argument("tables_path", help="Path to tables folder")
parser.add_argument("outfile", help="Path to xlsx output file")
args = parser.parse_args()


# define type of table to make and global variables for naming columns
mode = args.table_type
global type1, type2, type1_name, type2_name

# for 2 filetypes --> define type1, type2 and their column names in the output
if "_" in mode:
    type1 = mode.split("_")[0]
    type2 = mode.split("_")[1]
    if "AO" in type1:
        type1_name = "ASR output"
    elif "MT" in type1:
        type1_name = "Manual transcription"
    if "MT" in type2:
        type2_name = "Manual transcription"
    elif "PR" in type2:
        type2_name = "Prompt"
else:
    # no 2nd filetype --> process FD results
    type1 = mode
    type1_name = "Prompt"
    type2 = "conf"
    type2_name = "Confidence"

# to read
path_to_hyps = args.hypotheses_path
path_to_refs = args.references_path

# to write
path_to_xlsx_folder = args.tables_path
path_to_xlsx_sentences = path_to_xlsx_folder + args.outfile


def gen_dfs_and_xlsx(process_mode):
    """
    create a folder and generate df(s) from dict
    """
    Path(path_to_xlsx_folder).mkdir(parents=True, exist_ok=True)
    print("Processing files...")

    if process_mode == "FD":
        dict_sentences = create_general_dict(path_to_hyps)
    else:
        dict_sentences = create_general_dict(path_to_hyps, path_to_refs)
        
    generate_xlsx(dict_sentences, path_to_xlsx_sentences)
    print('Saved trans xlsx files to xlsx folder!')


def create_id_hyps_dict(folderpath):
    """
    create id hypothesis mapping
    """
    id_hyps_dict = {}
    id_conf_dict = {}

    for f in os.listdir(folderpath):
        if (f.endswith('.ort')) or (f.endswith('.wav.txt')) or (f.endswith('.ctm') and 'bestsym' not in f):
            with open(os.path.join(folderpath, f), 'r', encoding='UTF-8') as fin:
                lines = fin.readlines()
            file_id = f.split('.')[0]
            # print(file_id)
            text = ""
            confs = ""
            for line in range(len(lines)):
                if f.endswith('.ctm'):
                    if '<unk>' in lines[line]:
                        # print(file_id, lines[line])
                        text += ''
                    else:
                        text += lines[line].split(' ')[4] + ' '
                elif f.endswith('.ort'):
                    text += lines[line] + ' '
                elif "FD" in type1:
                    line_fields = lines[line].split('\t')
                    if len(line_fields) == 2:
                        if '<unk>' in line_fields[0]:
                            text += ''
                        else:
                            text += line_fields[0] + ' '
                            confs += str(line_fields[1]).strip('\n') + ' '

                hyp = text.replace('\n', '').replace('<unk>', '').rstrip(' ').replace('  ', ' ')
                id_hyps_dict[file_id] = hyp
                id_conf_dict[file_id] = confs
            # print(f"{file_id} trans = {id_hyps_dict[file_id]}")
    # print(len(id_hyps_dict))
    if "FD" in type1:
        return id_hyps_dict, id_conf_dict
    else:
        return id_hyps_dict


def create_id_refs_dict(folderpath):
    """
    create id reference mapping
    """
    id_refs_dict = {}

    for f in os.listdir(folderpath):
        if f.endswith('.prompt') or (f.endswith('.ort')):
            with open(os.path.join(folderpath, f), 'r', encoding='UTF-8') as fin:
                lines = fin.readlines()
            file_id = f.split('.')[0]
            for line in range(len(lines)):
                text = lines[line]

                # print(f"line ID = {file_id}, prompt = {repr(prompt)}")
                ref = text.replace('\n', '').replace('<unk>', '').rstrip(' ').replace('  ', ' ')
                id_refs_dict[file_id] = ref
            # print(f"{file_id} trans = {id_refs_dict[file_id]}")
    # print(len(id_refs_dict))
    return id_refs_dict


def create_general_dict(path_h, path_r=None):
    """
    for MT and AO processing:
    create a general dict
    dict {
    'wav_id001': {'reference': 'xxx', 'hypothesis': 'xxx'}
    'wav_id002': {'reference': 'xxx', 'hypothesis': 'xxx'}
    }

    for FD processing:
    create a dict
    dict {
    'wav_id_001': {'prompt': 'xxx', 'conf': ''###'}
    'wav_id_002': {'prompt': 'xxx', 'conf': ''###'}
    }
    """

    general_dict = {}

    if "FD" in type1:
        id_hyps_dict, id_conf_dict = create_id_hyps_dict(path_h)
        key_lst = list(id_hyps_dict.keys())
        for i in key_lst:
            general_dict[i] = {}
            ref = id_hyps_dict[i]
            conf = id_conf_dict[i]
            general_dict[i][type1_name] = ref
            general_dict[i][type2_name] = conf
    elif path_r:
        id_hyps_dict = create_id_hyps_dict(path_h)
        id_refs_dict = create_id_refs_dict(path_r)
        key_lst = list(id_hyps_dict.keys())
        for i in key_lst:
            general_dict[i] = {}
            ref = id_refs_dict[i]
            hyp = id_hyps_dict[i]
            general_dict[i][type1_name] = hyp
            general_dict[i][type2_name] = ref

    return general_dict


def generate_xlsx(dict_in, xlsx_path):
    """"
    If MT/AO: generate xlsx from dict with cols wav_id, prompt, trans
    If FD: generate xlsx from dict with cols wav_id, trans, conf
    """
    general_lst = []
    if "FD" in type1:
        for key, value in dict_in.items():
            prompt = value[type1_name]
            conf = value[type2_name]
            general_lst.append([key, prompt, conf])
        df = pd.DataFrame(general_lst)
        df.columns = ['wav_id', type1_name, type2_name]
        df.to_excel(xlsx_path, index=False)

    else:
        for key, value in dict_in.items():
            ref = value[type2_name]
            hyp = value[type1_name]
            general_lst.append([key, ref, hyp])
        df = pd.DataFrame(general_lst)
        df.columns = ['wav_id', type2_name, type1_name]
        df.to_excel(xlsx_path, index=False)


gen_dfs_and_xlsx(mode)
