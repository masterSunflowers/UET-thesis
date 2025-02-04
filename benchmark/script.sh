# prompt_builder.py
python prompt_builder.py \
    -i data/java_sampled.jsonl \
    -r /home/lvdthieu/Documents/Projects/benchmark_continue/java_repos_tmp \
    -o dev/test.jsonl \
    -l dev/log.jsonl \
    -m deepseek-coder \
    -lang java \
    -lg 1