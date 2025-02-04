import pandas as pd
from eval import cal_edit_sim, cal_exactly_match
# df = pd.read_json("data/python_dataset_cleaned.jsonl", lines=True)
# print(df.info())
df = pd.read_json("output/python_sampled_deepseek.jsonl", lines=True)
print(df.info())
references = df["groundtruth"].tolist()
preds = df["response"].fillna("").tolist()
em = cal_exactly_match(references, preds)
edit_sim = cal_edit_sim(references, preds)
print("==========RESULT==========")
print("EM:", "{:.2f}".format(em))
print("ES:", "{:.2f}".format(edit_sim))
print("==========================")
# for _, row in log0.iterrows():
#     for col in ["lsp_snippets", "import_snippets", "root_path_context_snippets"]:
#         if len(row[col]) > 0:
#             print(col)
# log1 = pd.read_json("log/java_sampled_prompt1.jsonl", lines=True)
#
# total = pd.concat([log0, log1], axis=0)
# total.info()
# total.reset_index(drop=True, inplace=True)
# # from pprint import pprint
# # pprint(total[total["built_prompt"].isnull()].index)
# # pprint(dict(total.loc[126]))
# # print("=" * 100)
# # pprint(dict(total.loc[304]))
# error = total[total["built_prompt"].isnull()]
# error.dropna(axis="columns", inplace=True, how="any")
# error.drop(columns=["model_name"], inplace=True)
# error.to_json("error.jsonl", orient="records", lines=True)
# done = total[~total["built_prompt"].isnull()]
# done.to_json("done.jsonl", orient="records", lines=True)

# done = pd.read_json("done.jsonl", lines=True)
# error = pd.read_json("error_prompt.jsonl", lines=True)
#
# complete = pd.concat([done, error], axis=0)
# complete.reset_index(drop=True, inplace=True)
# complete.info()
# complete.to_json("output/java_sampled_prompt.jsonl", orient="records", lines=True)