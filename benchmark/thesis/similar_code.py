from helper import Helper
from tree_sitter import Point
import os
import pandas as pd
from typing import List
EXTENSION = {
    "java": ".java",
    "python": ".py",
}
from utils import get_window_around_cursor, jaccard_similarity
from common_funcs import TOKENIZER, IRange

class SimilarCodeService:
    max_chunk_size = 128
    top_k = 10
    def __init__(self, cached_dir: str, tokenizer=TOKENIZER):
        self.tokenizer = tokenizer
        self.cached_dir = cached_dir
        if not os.path.exists(cached_dir):
            os.makedirs(cached_dir)
    
    def chunk_project(self, repo_dir: str, language: str):
        repo_name = repo_dir.split(os.path.sep)[-1]
        all_chunks = []
        for subdir, dirs, files in os.walk(repo_dir):
            for file in files:
                if file.endswith(EXTENSION[language]):
                    file_path = os.path.join(subdir, file)
                    chunks = self._chunk_code(file_path)
                    all_chunks.extend(chunks)
        pd.DataFrame(all_chunks).to_json(os.path.join(self.cached_dir, repo_name + ".jsonl"), orient="records", lines=True)

    
    def _chunk_code(self, file_path: str):
        with open(file_path, "r") as f:
            file_lines = f.readlines()
        chunks = []
        current_chunk = []
        current_token_count = 0
        start_line = 0
        for i, line in enumerate(file_lines):
            # Count tokens in the current line
            line_tokens = len(self.tokenizer(line)["input_ids"])
            # If this single line exceeds max_tokens, we need to handle it specially
            if line_tokens > self.max_chunk_size:
                # If there's content in the current chunk, finalize it
                if current_chunk:
                    chunks.append({
                        "content": "".join(current_chunk),
                        "range": IRange(start_point=Point(start_line, 0), end_point=Point(i, 0)).model_dump_json(),
                        "file_path": file_path
                    })
                    current_chunk = []
                    current_token_count = 0
                
                # Add the large line as its own chunk, potentially truncated
                chunks.append({
                    "content": line,
                    "range": IRange(start_point=Point(i, 0), end_point=Point(i + 1, 0)).model_dump_json(),
                    "file_path": file_path
                })
                
                # Reset for next chunk
                start_line = i + 1
            # If adding this line exceeds max_tokens and the chunk isn't empty, 
            # finalize the current chunk and start a new one    
            elif current_token_count + line_tokens > self.max_chunk_size and current_chunk:
                chunks.append({
                    "content": "".join(current_chunk),
                    "range": IRange(start_point=Point(start_line, 0), end_point=Point(i, 0)).model_dump_json(),  # end at previous line
                    "file_path": file_path
                })
                current_chunk = [line]
                current_token_count = line_tokens
                start_line = i
            else:
                # Add the line to the current chunk
                current_chunk.append(line)
                current_token_count += line_tokens
            
        # Add the last chunk if there's anything left
        if current_chunk:
            chunks.append({
                "content": "".join(current_chunk),
                "range": IRange(start_point=Point(start_line, 0), end_point=Point(len(file_lines), 0)).model_dump_json(),
                "file_path": file_path
            })
        return chunks


    def _get_candidates(self, repo_dir: str):
        repo_name = repo_dir.split(os.path.sep)[-1]
        cached_file_name = repo_name + ".jsonl"
        cached_file_path = os.path.join(self.cached_dir, cached_file_name)
        candidates = pd.read_json(cached_file_path, lines=True)
        return candidates
    
    def get_similar_code(self, helper: Helper):
        query_text = get_window_around_cursor(helper.cursor_index, helper.file_lines)
        encoded_query_text = self.tokenizer(query_text)["input_ids"]
        with open(helper.file_path, "r") as f:
            origin_content = f.read()
        with open(helper.file_path, "w") as f:
            f.write(helper.full_prefix + helper.full_suffix)
        self.chunk_project(helper.repo_dir, helper.language)
        candidates = self._get_candidates(helper.repo_dir)
        candidates["encoded"] = candidates["content"].apply(lambda candidate: self.tokenizer(candidate)["input_ids"])
        candidates["similarity"] = candidates["encoded"].apply(lambda candidate: jaccard_similarity(encoded_query_text, candidate))
        candidates = candidates.sort_values(by="similarity", ascending=False)
        with open(helper.file_path, "w") as f:
            f.write(origin_content)
        return candidates.head(self.top_k)[["content", "range", "file_path"]].to_dict(orient="records")