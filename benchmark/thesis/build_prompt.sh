#!/usr/bin/env bash
DIRNAME="$(dirname "$0")"
python "$DIRNAME/build_prompt.py" \
    --input "$DIRNAME/../../data/python_sampled.jsonl" \
    --repo-storage "/var/data/lvdthieu/thesis/data/python_repos_copy" \
    --output "$DIRNAME/../../data/python_sampled_thesis_prompt.jsonl" \
    --log "$DIRNAME/../../data/python_sampled_thesis_prompt_log.jsonl" \
    --model codestral-latest \
    --language python \
    --log-steps 1

