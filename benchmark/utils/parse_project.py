#   Author: masterSunflowers
#   Github: https://github.com/masterSunflowers/masterSunflowers
#   Date:   25/11/2024
#   Desc:   This file aims to parse a Java project and extract relevant information (class, method)
import argparse
import json
import os

import tree_sitter
import tree_sitter_java as tsjava
from tqdm import tqdm

JAVA = tree_sitter.Language(tsjava.language())
PARSER = tree_sitter.Parser(JAVA)


def normalize_code(code: str):
    lines_of_code = code.splitlines()
    redundant_space = len(lines_of_code[-1]) - 1
    for i in range(1, len(lines_of_code)):
        lines_of_code[i] = lines_of_code[i][redundant_space:]
    return "\n".join(lines_of_code)


def get_class_node_path(root_node: tree_sitter.Node, node: tree_sitter.Node):
    path = [node.child_by_field_name("name").text.decode("utf-8")]
    cur_node = node
    while cur_node.parent and cur_node.parent != root_node:
        cur_node = cur_node.parent
        if cur_node.type == "class_declaration":
            path.append(
                cur_node.child_by_field_name("name").text.decode("utf-8")
            )
    return ".".join(reversed(path))


def parse_java_files(directory: str):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                    tree = PARSER.parse(bytes(code, "utf-8"))
                    yield file_path, tree


def get_definitions(file_path: str, tree: tree_sitter.Tree):
    root_node = tree.root_node
    lst_class_info = []
    lst_method_info = []
    package_name = None

    # Get package of file
    for node in root_node.children:
        if node.type == "package_declaration":
            package_name = node.text.decode("utf-8")

    # Traverse root node children recursively to get class and method definitions
    stack = []
    for child in root_node.children:
        if child.type == "class_declaration":
            stack.append(child)
    while stack:
        node = stack.pop(0)
        if node.type == "class_declaration":
            tree_path = get_class_node_path(root_node, node)
            class_info = {
                "file_path": file_path,
                "definition": normalize_code(node.text.decode("utf-8")),
                "package": package_name,
                "tree_path": tree_path,
                "name": None,
                "modifiers": None,
                "superclass": None,
                "super_interfaces": None,
                "body": None,
            }
            class_body = None

            for child in node.named_children:
                if child.type == "identifier":
                    class_info["name"] = child.text.decode("utf-8")
                elif child.type == "modifiers":
                    class_info["modifiers"] = child.text.decode("utf-8")
                elif child.type == "superclass":
                    class_info["superclass"] = child.text.decode("utf-8")
                elif child.type == "super_interfaces":
                    class_info["super_interfaces"] = child.text.decode("utf-8")
                elif child.type == "class_body":
                    class_info["body"] = normalize_code(
                        child.text.decode("utf-8")
                    )
                    class_body = child

            lst_class_info.append(class_info)
            if class_body:
                for child in class_body.named_children:
                    if child.type == "method_declaration":
                        method_info = {
                            "file_path": file_path,
                            "definition": normalize_code(
                                child.text.decode("utf-8")
                            ),
                            "package": package_name,
                            "tree_path": tree_path,
                            "name": None,
                            "modifiers": None,
                            "return_type": None,
                            "parameters": [],
                            "body": None,
                        }
                        for c in child.named_children:
                            if c.type == "modifiers":
                                method_info["modifiers"] = c.text.decode(
                                    "utf-8"
                                )
                            elif c.type == "type_identifier":
                                method_info["return_type"] = c.text.decode(
                                    "utf-8"
                                )
                            elif c.type == "identifier":
                                method_info["name"] = c.text.decode("utf-8")
                                method_info["tree_path"] = (
                                    method_info["tree_path"]
                                    + ":"
                                    + method_info["name"]
                                )
                            elif c.type == "formal_parameters":
                                for param in c.named_children:
                                    if param.type == "formal_parameter":
                                        param_type = param.named_children[
                                            0
                                        ].text.decode("utf-8")
                                        param_name = param.named_children[
                                            1
                                        ].text.decode("utf-8")
                                        method_info["parameters"].append(
                                            {
                                                "type": param_type,
                                                "name": param_name,
                                            }
                                        )
                            elif c.type == "block":
                                method_info["body"] = normalize_code(
                                    c.text.decode("utf-8")
                                )
                        lst_method_info.append(method_info)
                    elif child.type == "class_declaration":
                        stack.append(child)
                    elif child.type == "constructor_declaration":
                        constructor_info = {
                            "file_path": file_path,
                            "definition": normalize_code(
                                child.text.decode("utf-8")
                            ),
                            "package": package_name,
                            "tree_path": tree_path,
                            "name": None,
                            "modifiers": None,
                            "parameters": [],
                            "body": None,
                            "constructor": True,
                        }
                        for c in child.named_children:
                            if c.type == "modifiers":
                                constructor_info["modifiers"] = c.text.decode(
                                    "utf-8"
                                )
                            elif c.type == "identifier":
                                constructor_info["name"] = c.text.decode(
                                    "utf-8"
                                )
                                constructor_info["tree_path"] = (
                                    constructor_info["tree_path"]
                                    + ":"
                                    + constructor_info["name"]
                                )
                            elif c.type == "formal_parameters":
                                for param in c.named_children:
                                    if param.type == "formal_parameter":
                                        param_type = param.named_children[
                                            0
                                        ].text.decode("utf-8")
                                        param_name = param.named_children[
                                            1
                                        ].text.decode("utf-8")
                                        constructor_info["parameters"].append(
                                            {
                                                "type": param_type,
                                                "name": param_name,
                                            }
                                        )
                            elif c.type == "constructor_body":
                                constructor_info["body"] = normalize_code(
                                    c.text.decode("utf-8")
                                )
                        lst_method_info.append(constructor_info)
    return lst_class_info, lst_method_info


def main(args):
    lst_repo = os.listdir(args.repos_dir)
    for repo in tqdm(lst_repo):
        repo_dir = os.path.join(args.repos_dir, repo)
        all_class = []
        all_method = []
        for file_path, tree in parse_java_files(repo_dir):
            rev_path = os.path.relpath(file_path, repo_dir)
            lst_class_info, lst_method_info = get_definitions(rev_path, tree)
            all_class.extend(lst_class_info)
            all_method.extend(lst_method_info)
        if not os.path.exists(os.path.join(args.output_dir, repo)):
            os.makedirs(os.path.join(args.output_dir, repo))
        with open(
            os.path.join(args.output_dir, repo, "class_info.json"), "w"
        ) as f:
            json.dump(all_class, f, indent=4)
        with open(
            os.path.join(args.output_dir, repo, "method_info.json"), "w"
        ) as f:
            json.dump(all_method, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repos-dir", dest="repos_dir")
    parser.add_argument("--output-dir", dest="output_dir")
    args = parser.parse_args()

    main(args)