import re
from typing import Optional, List
from textwrap import dedent
import tree_sitter
import tree_sitter_java as tsjava
import tree_sitter_python as tspython
from transformers import LlamaTokenizerFast
from tree_sitter import Node, Point, Tree
from pydantic import BaseModel
import os
import dotenv
import logging

dotenv.load_dotenv(override=True)

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
    ],
}
LANGUAGE_COMMENT_SYMBOL = {
    "java": "//",
    "python": "#",
}
COMMON_STOPS = ["/src", "#- coding: utf-8", "```"]
FUNCTION_BLOCK_NODE_TYPES = ["block", "statement_block"]
JAVA_PARSER = tree_sitter.Parser(language=JAVA)
PYTHON_PARSER = tree_sitter.Parser(language=PYTHON)
TOP_LEVEL_KEY_WORDS = {"java": ["class", "function"], "python": ["def", "class", "\"\"\"#"]}
TOKENIZER = LlamaTokenizerFast.from_pretrained("hf-internal-testing/llama-tokenizer", token=os.getenv(""))
TYPES_TO_USE = {
    "arrow_function",
    "generator_function_declaration"
    "program", 
    "function_declaration",
    "function_definition",
    "method_definition",
    "method_declaration",
    "class_declaration",
    "class_definition"
}
QUERIES = {
    "root_path_context_queries": {
        "python": {
            "class_definition": dedent("""
; Match superclass identifiers in a simple inheritance
(class_definition
  superclasses: (argument_list
    (identifier) @catch)
  (#not-match? @catch "^(str|int|float|bool|list|dict|tuple|set|frozenset|complex|bytes|bytearray|memoryview|range|slice|object|type|NoneType|List|Dict|Tuple|Set|FrozenSet|Union|Optional|Any|Callable|Iterable|Iterator|Generator|Coroutine|AsyncIterable|AsyncIterator|Awaitable|ContextManager|Pattern|Match|TypeVar|Generic|Sequence|Mapping|MutableMapping|MutableSequence|ByteString|Reversible|Sized|Container|Collection|AbstractSet|MutableSet|KeysView|ItemsView|ValuesView|Hashable|Sized|SupportsInt|SupportsFloat|SupportsComplex|SupportsBytes|SupportsAbs|SupportsRound|ChainMap|Counter|OrderedDict|defaultdict|deque|namedtuple|TypedDict)$")
)

; Match the value of a keyword argument in class inheritance
(class_definition
  superclasses: (argument_list
    (keyword_argument
      (_)
      (identifier) @catch))
  (#not-match? @catch "^(str|int|float|bool|list|dict|tuple|set|frozenset|complex|bytes|bytearray|memoryview|range|slice|object|type|NoneType|List|Dict|Tuple|Set|FrozenSet|Union|Optional|Any|Callable|Iterable|Iterator|Generator|Coroutine|AsyncIterable|AsyncIterator|Awaitable|ContextManager|Pattern|Match|TypeVar|Generic|Sequence|Mapping|MutableMapping|MutableSequence|ByteString|Reversible|Sized|Container|Collection|AbstractSet|MutableSet|KeysView|ItemsView|ValuesView|Hashable|Sized|SupportsInt|SupportsFloat|SupportsComplex|SupportsBytes|SupportsAbs|SupportsRound|ChainMap|Counter|OrderedDict|defaultdict|deque|namedtuple|TypedDict)$")
)

; Match identifiers within subscripts in class inheritance
(class_definition
  superclasses: (argument_list
    (subscript
      (identifier) @catch
    ))
  (#not-match? @catch "^(str|int|float|bool|list|dict|tuple|set|frozenset|complex|bytes|bytearray|memoryview|range|slice|object|type|NoneType|List|Dict|Tuple|Set|FrozenSet|Union|Optional|Any|Callable|Iterable|Iterator|Generator|Coroutine|AsyncIterable|AsyncIterator|Awaitable|ContextManager|Pattern|Match|TypeVar|Generic|Sequence|Mapping|MutableMapping|MutableSequence|ByteString|Reversible|Sized|Container|Collection|AbstractSet|MutableSet|KeysView|ItemsView|ValuesView|Hashable|Sized|SupportsInt|SupportsFloat|SupportsComplex|SupportsBytes|SupportsAbs|SupportsRound|ChainMap|Counter|OrderedDict|defaultdict|deque|namedtuple|TypedDict)$")    
)
            """),
            "function_definition": dedent("""
; When the type is a simple identifier:
(function_definition
  parameters: (parameters
    (typed_parameter
      type: (type
              (identifier) @type_identifier)))

  (#not-match? @type_identifier "^(str|int|float|bool|list|dict|tuple|set|frozenset|complex|bytes|bytearray|memoryview|range|slice|object|type|NoneType|List|Dict|Tuple|Set|FrozenSet|Union|Optional|Any|Callable|Iterable|Iterator|Generator|Coroutine|AsyncIterable|AsyncIterator|Awaitable|ContextManager|Pattern|Match|TypeVar|Generic|Sequence|Mapping|MutableMapping|MutableSequence|ByteString|Reversible|Sized|Container|Collection|AbstractSet|MutableSet|KeysView|ItemsView|ValuesView|Hashable|Sized|SupportsInt|SupportsFloat|SupportsComplex|SupportsBytes|SupportsAbs|SupportsRound|ChainMap|Counter|OrderedDict|defaultdict|deque|namedtuple|TypedDict)$")
)

; When the type is a generic type with one identifier
(function_definition
  parameters: (parameters
    (typed_parameter
      type: (type
              (generic_type
                (identifier) @type_identifier))))

  (#not-match? @type_identifier "^(str|int|float|bool|list|dict|tuple|set|frozenset|complex|bytes|bytearray|memoryview|range|slice|object|type|NoneType|List|Dict|Tuple|Set|FrozenSet|Union|Optional|Any|Callable|Iterable|Iterator|Generator|Coroutine|AsyncIterable|AsyncIterator|Awaitable|ContextManager|Pattern|Match|TypeVar|Generic|Sequence|Mapping|MutableMapping|MutableSequence|ByteString|Reversible|Sized|Container|Collection|AbstractSet|MutableSet|KeysView|ItemsView|ValuesView|Hashable|Sized|SupportsInt|SupportsFloat|SupportsComplex|SupportsBytes|SupportsAbs|SupportsRound|ChainMap|Counter|OrderedDict|defaultdict|deque|namedtuple|TypedDict)$")
)

; When the generic type has type parameters with one identifier
(function_definition
  parameters: (parameters
    (typed_parameter
      type: (type
              (generic_type
                (identifier)
                (type_parameter
                  (type
                    (identifier) @type_identifier))))))

  (#not-match? @type_identifier "^(str|int|float|bool|list|dict|tuple|set|frozenset|complex|bytes|bytearray|memoryview|range|slice|object|type|NoneType|List|Dict|Tuple|Set|FrozenSet|Union|Optional|Any|Callable|Iterable|Iterator|Generator|Coroutine|AsyncIterable|AsyncIterator|Awaitable|ContextManager|Pattern|Match|TypeVar|Generic|Sequence|Mapping|MutableMapping|MutableSequence|ByteString|Reversible|Sized|Container|Collection|AbstractSet|MutableSet|KeysView|ItemsView|ValuesView|Hashable|Sized|SupportsInt|SupportsFloat|SupportsComplex|SupportsBytes|SupportsAbs|SupportsRound|ChainMap|Counter|OrderedDict|defaultdict|deque|namedtuple|TypedDict)$")
)

; When the return type is a simple identifier
(function_definition
  return_type: (type
    (identifier) @type_identifier)
  (#not-match? @type_identifier "^(str|int|float|bool|list|dict|tuple|set|frozenset|complex|bytes|bytearray|memoryview|range|slice|object|type|NoneType|List|Dict|Tuple|Set|FrozenSet|Union|Optional|Any|Callable|Iterable|Iterator|Generator|Coroutine|AsyncIterable|AsyncIterator|Awaitable|ContextManager|Pattern|Match|TypeVar|Generic|Sequence|Mapping|MutableMapping|MutableSequence|ByteString|Reversible|Sized|Container|Collection|AbstractSet|MutableSet|KeysView|ItemsView|ValuesView|Hashable|Sized|SupportsInt|SupportsFloat|SupportsComplex|SupportsBytes|SupportsAbs|SupportsRound|ChainMap|Counter|OrderedDict|defaultdict|deque|namedtuple|TypedDict)$")
)

; When the return type is a generic type with one identifier
(function_definition
  return_type: (type
    (generic_type
      (identifier) @type_identifier))
  (#not-match? @type_identifier "^(str|int|float|bool|list|dict|tuple|set|frozenset|complex|bytes|bytearray|memoryview|range|slice|object|type|NoneType|List|Dict|Tuple|Set|FrozenSet|Union|Optional|Any|Callable|Iterable|Iterator|Generator|Coroutine|AsyncIterable|AsyncIterator|Awaitable|ContextManager|Pattern|Match|TypeVar|Generic|Sequence|Mapping|MutableMapping|MutableSequence|ByteString|Reversible|Sized|Container|Collection|AbstractSet|MutableSet|KeysView|ItemsView|ValuesView|Hashable|Sized|SupportsInt|SupportsFloat|SupportsComplex|SupportsBytes|SupportsAbs|SupportsRound|ChainMap|Counter|OrderedDict|defaultdict|deque|namedtuple|TypedDict)$")
)

; When the generic type has type parameters with one identifier
(function_definition
  return_type: (type
    (generic_type
      (identifier)
      (type_parameter
        (type
          (identifier) @type_identifier))))
  (#not-match? @type_identifier "^(str|int|float|bool|list|dict|tuple|set|frozenset|complex|bytes|bytearray|memoryview|range|slice|object|type|NoneType|List|Dict|Tuple|Set|FrozenSet|Union|Optional|Any|Callable|Iterable|Iterator|Generator|Coroutine|AsyncIterable|AsyncIterator|Awaitable|ContextManager|Pattern|Match|TypeVar|Generic|Sequence|Mapping|MutableMapping|MutableSequence|ByteString|Reversible|Sized|Container|Collection|AbstractSet|MutableSet|KeysView|ItemsView|ValuesView|Hashable|Sized|SupportsInt|SupportsFloat|SupportsComplex|SupportsBytes|SupportsAbs|SupportsRound|ChainMap|Counter|OrderedDict|defaultdict|deque|namedtuple|TypedDict)$")
)
            """)
        },
        "java": {
            "method_declaration": dedent("""
; Method parameters
(method_declaration
  (formal_parameters
    (formal_parameter
    	(type_identifier) @a
    )
  )
)

; Return type
(method_declaration
  (type_identifier) @b
)
            """)
        }
    },
    "import_queries": {
        "python": dedent("""
(import_from_statement
  (dotted_name) ; skip the first (this is the module)
  (dotted_name
    (identifier) @importa))

(import_statement
    (dotted_name
        (identifier) @importb ))
        """),
        "java": dedent("""
(import_declaration
  (scoped_identifier
    (identifier) @import))
        """)
    }
}
SEP_REGEX = r"[\\/]"

# Checked
class IRange(BaseModel):
    """Range in a file, from start_point to end_point"""
    start_point: Point
    end_point: Point


# Checked
def get_ast(content: str, language: str):
    """Returns the AST of the given content in the given language"""
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
        logging.error(f"Get AST error:\n{e}")
        return None


# Checked
def get_symbols_for_snippet(text: str) -> List[str]:
    """Get all symbols in the given text"""
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
def get_tree_sitter_query(query_type: str, language: str, node_type: Optional[str] = None):
    if query_type == "root_path_context_queries":
        if language == "java":
            return JAVA.query(QUERIES[query_type][language][node_type]) if QUERIES[query_type][language].get(node_type, None) else None
        elif language == "python":
            return PYTHON.query(QUERIES[query_type][language][node_type]) if QUERIES[query_type][language].get(node_type, None) else None
    elif query_type == "import_queries":
        if language == "java":
            return JAVA.query(QUERIES[query_type][language])
        elif language == "python":
            return PYTHON.query(QUERIES[query_type][language])
    return None


# Checked
def get_tree_path_at_cursor(ast: Tree, cursor_index: Point) -> List[Node]:
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
    """Reads a range of text from a file."""
    with open(file_path, "r") as f:
        lines = f.read().splitlines()

    content = ""
    for line in lines[range.start_point.row : range.end_point.row]:
        content += line + "\n"
    content += lines[range.end_point.row][: range.end_point.column]
    return content


# Need fix
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


# Checked
def point2index(content: str, point: Point) -> int:
    content = content.replace("\r\n", "\n")
    lines = content.splitlines()
    index = 0
    for i in range(point.row):
        index += len(lines[i]) + 1
    index += point.column
    return index


# Checked
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


# Need fix
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
