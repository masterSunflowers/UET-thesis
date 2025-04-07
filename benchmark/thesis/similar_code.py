from helper import Helper
from tree_sitter import Point
import os

EXTENSION = {
    "java": ".java",
    "python": ".py",
}
class SimilarCodeService:
    def __init__(self):
        pass

    def chunking_code(self, helper: Helper):
        directory  =  helper.repo_dir
        for subdir, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(EXTENSION[helper.language]):
                    file_path = os.path.join(subdir, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                        chunks = self.chunking_code(content)
    def get_similar_code(self, cursor: Point):
        pass