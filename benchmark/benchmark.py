import argparse
import pandas as pd
from eval import cal_edit_sim, cal_exactly_match

def main(args):
    df = pd.read_json(args.input, lines=True)
    references = df["groundtruth"].tolist()
    preds = df["predict"].fillna("").tolist()   # preds = df["completions"].fillna("").tolist()
    em = cal_exactly_match(references, preds)
    edit_sim = cal_edit_sim(references, preds)
    print("==========RESULT==========")
    print("EM:", "{:.4f}".format(em))
    print("ES:", "{:.2f}".format(edit_sim))
    print("==========================")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, dest="input")
    args = parser.parse_args()
    main(args)


# 19.15 62.81
# 27.66 75.17
