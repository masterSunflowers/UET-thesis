import argparse
import pandas as pd
from prompt import get_completion
from eval import cal_edit_sim, cal_exactly_match

def main(args):
    df = pd.read_json(args.input, lines=True)
    df["task_id"] = df["metadata"].apply(lambda x: x["task_id"])
    prefixes = df["prefix"].tolist()
    suffixes = df["suffix"].tolist()
    prompts = df["build_prompt"].tolist()
    preds = get_completion(prefixes, suffixes, prompts, args.model)
    df["response"] = preds
    df.to_json(args.output, orient="records", lines=True)
    references = df["groundtruth"].tolist()
    preds = df["response"].fillna("").tolist()
    em = cal_exactly_match(references, preds)
    edit_sim = cal_edit_sim(references, preds)
    print("==========RESULT==========")
    print("EM:", "{:.2f}".format(em))
    print("ES:", "{:.2f}".format(edit_sim))
    print("==========================")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, dest="input")
    parser.add_argument("-o", "--output", type=str, dest="output")
    parser.add_argument("-m", "--model", type=str, dest="model", default="deepseek-coder")
    args = parser.parse_args()
    main(args)
