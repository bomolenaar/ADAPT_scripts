## ADAPT_scripts

Scripts I use to align transcriptions of speech and score the alignment.

# Call as follows:

1.  gen_dfs_BM.py           --> creates a .xlsx file with columns `wav_id` (=filename), `reference` (=gold standard), `hypothesis` (=attempt transcript).
    Possible modes: `MT_PR, AO_PR, AO_MT, (FD)`.
2.  computeAlignments_BM.py --> performs ADAPT alignment for colums `reference` and `hypothesis` in provided .xlsx file, outputs word-level scored alignment.
3.  ADAPT_scoring.py        --> calculates file-level binary correctness and kappa score for cols `reference` and `hypothesis`.
