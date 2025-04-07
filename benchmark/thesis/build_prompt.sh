python /var/data/lvdthieu/thesis/benchmark/thesis/build_prompt.py \
    --input /var/data/lvdthieu/thesis/data/java_sampled.jsonl \
    --repo-storage /var/data/lvdthieu/thesis/data/java_repos_copy \
    --output /var/data/lvdthieu/thesis/data/java_sampled_thesis_prompt.jsonl \
    --log /var/data/lvdthieu/thesis/data/java_sampled_thesis_prompt_log.jsonl \
    --model codestral-latest \
    --language java \
    --log-steps 1 
    # --debug

