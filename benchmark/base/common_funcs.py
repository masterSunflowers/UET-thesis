import re
from typing import Optional, List

import tree_sitter
import tree_sitter_java as tsjava
import tree_sitter_python as tspython
from transformers import AutoTokenizer
from tree_sitter import Node, Point, Tree
from pydantic import BaseModel

JAVA = tree_sitter.Language(tsjava.language())
PYTHON = tree_sitter.Language(tspython.language())
LANG_EXTENSIONS = {"java": ".java", "python": ".py"}
FUNCTION_DECLARATION_NODE_TYPES = [
    "method_definition",
    "function_definition",
    "function_item",
    "function_declaration",
    "method_declaration",
]
TREE_SITTER_NODE_TYPES = {
    "method": FUNCTION_DECLARATION_NODE_TYPES,
    "type": [
        "class_declaration",
        "class_definition",
        "interface_declaration",
        "enum_declaration",
        "record_declaration",
    ],
}
LANGUAGE_COMMENT_SYMBOL = {
    "java": "//",
    "python": "#",
    "javascript": "//",
    "typescript": "//",
    "csharp": "//",
}
COMMON_STOPS = ["/src", "#- coding: utf-8", "```"]
FUNCTION_BLOCK_NODE_TYPES = ["block", "statement_block"]
JAVA_PARSER = tree_sitter.Parser(language=JAVA)
PYTHON_PARSER = tree_sitter.Parser(language=PYTHON)
TOP_LEVEL_KEY_WORDS = {"java": ["class", "function"], "python": ["def", "class"]}
TOKENIZER = AutoTokenizer.from_pretrained("Salesforce/codegen-6B-mono")
TYPES_TO_USE = {"program", "function_declaration", "method_definition"}
QUERIES = {
    "java": {
        "import_query": "(import_declaration\n  (scoped_identifier\n    (identifier) @import))",
        "method_declaration": """; Method parameters\n(method_declaration\n  (formal_parameters\n    (formal_parameter\n    \t(type_identifier) @a\n    )\n  )\n)\n\n; Return type\n(method_declaration\n  (type_identifier) @b\n)"""
    },
    
    "python": {
        "import_query": """(import_from_statement\n  (dotted_name) ; skip the first (this is the module)\n  (dotted_name\n    (identifier) @importa))\n\n(import_statement\n    (dotted_name\n        (identifier) @importb ))""",
        "function_declartion": """(\n    (function_definition\n        (parameters \n            (_ \n                (type) @a\n                (#not-match? @a "^(str|int|float|bool|list|dict|tuple)$")\n            )\n        )\n    )\n)\n\n(\n    (function_definition\n        (type) @b\n        (#not-match? @b "^(str|int|float|bool|list|dict|tuple)$")\n    )\n)"""
    }
}
SEP_REGEX = r"[\\/]"

# Checked
class IRange(BaseModel):
    start_point: Point
    end_point: Point


# Checked
def get_ast(content, language):
    if language == "java":
        parser = JAVA_PARSER
    elif language == "python":
        parser = PYTHON_PARSER
    else:
        raise NotImplementedError("Language is not currently supported")
    try:
        ast = parser.parse(bytes(content, encoding="utf-8"))
        return ast
    except Exception as e:
        print(e)
        return None


# Checked
def get_symbols_for_snippet(text):
    symbols = set(
        filter(
            lambda s: s != "",
            map(
                lambda s: s.strip(),
                re.split(r"[\s.,/#!$%^&*;:{}=\-_`~()\[\]]", text),
            ),
        )
    )
    return symbols


# Checked
def get_tree_sitter_query(language: str, query_type: str):
    if language == "java":
        return JAVA.query(QUERIES[language][query_type])
    elif language == "python":
        return PYTHON.query(QUERIES[language][query_type])


def get_tree_path_at_cursor(ast: Tree, cursor_index: Point):
    path = [ast.root_node]
    while path[-1].child_count > 0:
        found_child = False
        for child in path[-1].children:
            if child.start_point <= cursor_index <= child.end_point:
                path.append(child)
                found_child = True
                break
        if not found_child:
            break
    return path


# Checked
def find_children(node: Node, predicate, first_n: Optional[int] = None):
    matching_nodes = []
    if first_n and first_n <= 0:
        return []

    # Check if the current node's type is in the list of types we're interested in
    if predicate(node):
        matching_nodes.append(node)

    # Recursively search for matching types in all children of the current node
    for child in node.children:
        matching_nodes.extend(
            find_children(
                child, predicate, first_n - len(matching_nodes) if first_n else None
            )
        )

    return matching_nodes


# Checked
def read_range_in_file(file_path: str, range: IRange):
    with open(file_path, "r") as f:
        lines = f.read().splitlines()

    content = ""
    for line in lines[range.start_point.row : range.end_point.row]:
        content += line + "\n"
    content += lines[range.end_point.row][: range.end_point.column]
    return content


def find_type_identifiers(root_node: Node) -> List[Node]:
    return find_children(
        root_node,
        lambda node: node.type == "type_identifier"
        or (
            node.parent
            and node.parent.type == "ERROR"
            and node.type == "identifier"
            and node.text.decode("utf-8")[0].isupper()
        ),
    )


def point2index(content: str, point: Point) -> int:
    content = content.replace("\r\n", "\n")
    lines = content.splitlines()
    index = 0
    for i in range(point.row):
        index += len(lines[i]) + 1
    index += point.column
    return index


def lsprange2irange(lsprange: dict) -> IRange:
    return IRange(
        start_point=Point(
            row=lsprange["start"]["line"],
            column=lsprange["start"]["character"],
        ),
        end_point=Point(
            row=lsprange["end"]["line"], column=lsprange["end"]["character"]
        ),
    )


# Checked
def intersection(a: IRange, b: IRange) -> Optional[IRange]:
    start_row = max(a.start_point.row, b.start_point.row)
    end_row = min(a.end_point.row, b.end_point.row)
    if start_row > end_row:
        return None

    if start_row == end_row:
        start_column = max(a.start_point.column, b.start_point.column)
        end_column = min(a.end_point.column, b.end_point.column)

        if start_column > end_column:
            return None

        return IRange(
            start_point=Point(row=start_row, column=start_column),
            end_point=Point(row=end_row, column=end_column),
        )

    start_column = (
        a.start_point.column if start_row == a.start_point.row else b.start_point.column
    )
    end_column = (
        a.end_point.column if end_row == a.end_point.row else b.end_point.column
    )

    return IRange(
        start_point=Point(row=start_row, column=start_column),
        end_point=Point(row=end_row, column=end_column),
    )
