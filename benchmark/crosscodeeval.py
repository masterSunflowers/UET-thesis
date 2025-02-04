#!/usr/bin/env python
# coding: utf-8

# # Check, make and clean dataset

# In[1]:


import pandas as pd

df = pd.read_json("CrossCodeEval/typescript/line_completion.jsonl", lines=True)
df.info()


# In[2]:


for col in df.columns:
    print(df.loc[0, col])


# In[23]:


df["repo"] = df["metadata"].apply(lambda x: x["repository"])


# In[24]:


df["repo"].unique()


# In[25]:


lst_repo = df["repo"].unique().tolist()
lst_repo


# In[26]:


df["commit"] = df["repo"].apply(lambda name: name.split('-')[-1])


# In[27]:


lst_candidate = []
for repo in lst_repo:
    lst = repo.split('-')[:-1]
    for i in range(0, len(lst) - 1):
        username = '-'.join(lst[:i + 1])
        repo = '-'.join(lst[i + 1:])
        lst_candidate.append({"username": username, "repo": repo})
print(len(lst_candidate))


# In[ ]:


import requests
import time
from tqdm import tqdm
HEADER = {
    'Authorization': '<TOKEN>', 
    'Accept': 'application/vnd.github.v3+json'
}
for i, candidate in tqdm(enumerate(lst_candidate), total=len(lst_candidate), desc="Querying"):
    try:
        url = f"https://api.github.com/repos/{candidate['username']}/{candidate['repo']}"
        response = requests.get(url, headers=HEADER)
        if response.status_code == 404:
            lst_candidate[i]["exists"] = False
        elif response.status_code == 200:
            lst_candidate[i]["exists"] = True
        else:
            print(response.status_code)
    except Exception as e:
        print(candidate)
        print(e)
        print('-' * 100)
    time.sleep(0.72)


# In[39]:


lst_candidate[0]


# In[37]:


lst_candate_filter = list(filter(lambda candidate: candidate["exists"], lst_candidate))
len(lst_candate_filter)


# In[32]:


df["repo"]


# In[38]:


for i in range(len(lst_candate_filter)):
    lst_candate_filter[i]["origin"] = lst_candate_filter[i]["username"] + '-' + lst_candate_filter[i]["repo"]

lst_candate_filter


# In[40]:


def repo_to_encode(repo: str):
    commit = repo.split('-')[-1]
    origin = '-'.join(repo.split('-')[:-1])
    for candidate in lst_candate_filter:
        if origin == candidate["origin"]:
            encode = candidate["username"] + "--" + candidate["repo"] + "--" + commit
            return encode
    return None


# In[44]:


i = 75
print(df.loc[i, "repo"])
repo_to_encode(df.loc[i, "repo"])


# In[45]:


df["encode"] = df["repo"].apply(lambda repo: repo_to_encode(repo))


# In[47]:


df["encode"].info()


# In[48]:


df.info()


# In[49]:


new_df = df.dropna(axis=0, how="any", ignore_index=True)


# In[50]:


new_df.info()


# In[51]:


new_df.to_json("dataset.jsonl", lines=True, orient="records")


# In[53]:


new_df["encode"].nunique()


# In[54]:


lst_encode = new_df["encode"].unique().tolist()


# In[ ]:


import collections
repo = [encode.split("--")[1] for encode in lst_encode]
collections.Counter(repo)


# In[58]:


import subprocess
tmp_df = new_df.drop_duplicates(subset=["encode"], ignore_index=True)
save_dir="/home/lvdthieu/Documents/Projects/benchmark_continue/github_repos"
for _, row in tqdm(tmp_df.iterrows(), total=len(tmp_df), desc="Cloning"):
    encode = row["encode"]
    username, repo, commit = encode.split("--")
    cmd = f"cd {save_dir} && mv {repo} {encode}"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)


# In[62]:


for row in tmp_df[tmp_df["encode"].str.contains("android_device_xiaomi_sm6225-common")]["encode"]:
    print(row)


# In[65]:


new_new_df = new_df[new_df["encode"] != "CHRISL7--android_device_xiaomi_sm6225-common--ed8a1e0"]
new_new_df.info()


# In[66]:


new_new_df.reset_index(drop=True, inplace=True)
new_new_df.info()


# In[67]:


new_new_df.to_json("dataset_cleaned.jsonl", lines=True, orient="records")


# # New

# In[14]:


import pandas as pd
df = pd.read_json("data/dataset_cleaned.jsonl", lines=True)
df.info()


# In[15]:


sampled = df.sample(n=200, random_state=42)
sampled


# In[16]:


sampled.to_json("data/dataset_sampled.jsonl", lines=True, orient="records")


# In[ ]:




