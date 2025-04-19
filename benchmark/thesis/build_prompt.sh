#!/usr/bin/env bash
DIRNAME="$(dirname "$0")"
python "$DIRNAME/build_prompt.py" \
    --input "$DIRNAME/../../data/java_sampled.jsonl" \
    --repo-storage "/home/lvdthieu/Documents/Projects/UET-thesis/data/java_repos_copy" \
    --output "$DIRNAME/../../data/java_sampled_thesis_prompt.jsonl" \
    --log "$DIRNAME/../../data/java_sampled_thesis_prompt_log.jsonl" \
    --model codestral-latest \
    --language java \
    --log-steps 1 \
    --debug

