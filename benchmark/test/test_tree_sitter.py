import os
import sys
import tree_sitter
import tree_sitter_java as tsjava
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
JAVA = tree_sitter.Language(tsjava.language()) 
CWD = os.path.abspath(os.path.dirname(__file__))
df = pd.read_json(os.path.join(CWD, "..", "data", "dataset_cleaned.jsonl"), lines=True)


def get_abs_path(repo_dir: str, repo_encode: str, rev_path: str):
    return os.path.join(repo_dir, repo_encode, rev_path)


file_path = get_abs_path(
    os.path.join(CWD, "..", "github_repos_tmp"),
    df.loc[0, "encode"],
    df.loc[0]["metadata"]["file"],
)

file_path = "/home/lvdthieu/Documents/Projects/benchmark_continue/github_repos_tmp/akang943578--java-bard-api--7352c25/src/main/java/com/api/bard/BardClient.java"
# file_path = "/home/lvdthieu/Documents/Projects/benchmark_continue/github_repos_tmp/AADevelops--JaGame--fc2ae51/jagame/GraphicsPanel.java"
with open(file_path, "r") as f:
    file_content = f.read()

parser = tree_sitter.Parser(language=JAVA)
file_content = """class LowercaseStringProperty{\n\tpublic LowercaseStringProperty(final String jsonName, final String dbName, final PropertyValidator<String>... validators)
 {\n\n\tsuper(jsonName);\n\tthis.dbName = dbName;\n\n\tfor (PropertyValidator<String> validator : validators) {\n\t\taddValidator(validat
or);\n\t}\n}\t}
"""
ast = parser.parse(bytes(file_content, encoding="utf-8"))
root = ast.root_node
CLASS_LIKE = ["class_declaration", "interface_declaration", "record_declaration"]
class_node = None
# print(root)
for child in root.children:
    if child.type == "class_declaration":
        class_node = child
        break
# # print(class_node)
for child in class_node.named_children:
    if child.type == "class_body":
        for c in child.named_children:
            if c.type == "constructor_declaration":
                print(c.child_by_field_name("parameters"))
# print(root)

            

# file_path = "/home/lvdthieu/Documents/Projects/continue/manual-testing-sandbox/thieulvd/test/Calculator.java"
# import_service = ImportService(
#     # repo_dir="/home/lvdthieu/Documents/Projects/benchmark_continue/github_repos_tmp/AADevelops--JaGame--fc2ae51clear",
#     repo_dir="/home/lvdthieu/Documents/Projects/continue/manual-testing-sandbox",
#     language="java"
# )

# print(import_service.get_file_info(file_path))

# file_path = "/home/lvdthieu/Documents/Projects/continue/manual-testing-sandbox/thieulvd/test/Calculator.java"
# import_service = ImportService(
#     # repo_dir="/home/lvdthieu/Documents/Projects/benchmark_continue/github_repos_tmp/AADevelops--JaGame--fc2ae51clear",
#     repo_dir="/home/lvdthieu/Documents/Projects/benchmark_continue/github_repos_tmp/AADevelops--JaGame--fc2ae51",
#     language="java"
# )

# print(import_service.get_file_info(file_path))
