# from transformers import LlamaTokenizer
# import sqlite3

# conn = sqlite3.connect("/home/lvdthieu/.continue/index/index.sqlite")
# cur = conn.cursor()

# tokenizer = LlamaTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf")

# res = cur.execute("SELECT content FROM chunks WHERE INSTR(path, '/home/lvdthieu/Documents/Projects/UET-thesis') > 0").fetchall()
# for r in res:
#     print(len(tokenizer.tokenize(r[0])))
