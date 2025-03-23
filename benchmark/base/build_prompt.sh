python build_prompt.py \
    --input ../data/java_sampled.jsonl \
    --repo-storage /home/lvdthieu/Documents/Projects/UET-thesis/benchmark/data/java_repos_copy \
    --output ../data/java_sampled_prompt.jsonl \
    --log ../data/java_sampled_prompt.log \
    --model codestral-latest \
    --language java \
    --log-steps 1

