from abc import ABC
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser
from .language_enum import LanguageEnum, LANGUAGE_QUERIES
from .nodes import TreesitterClassNode, TreesitterMethodNode
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")



class Treesitter(ABC):
    """
    Abstract base class for parsing source code using tree-sitter.
    Provides functionality to extract class and method information from source files.
    """
    
    def __init__(self, language: LanguageEnum):
        """
        Initialize the Treesitter parser for a specific programming language.

        Args:
            language (LanguageEnum): The programming language to parse
        
        Raises:
            ValueError: If the specified language is not supported
        """
        self.language_enum = language
        self.parser = get_parser(language.value)
        self.language_obj = get_language(language.value)
        self.query_config = LANGUAGE_QUERIES.get(language)
        if not self.query_config:
            raise ValueError(f"Unsupported language: {language}")

        # Corrected query instantiation
        self.class_query = self.language_obj.query(self.query_config['class_query'])
        self.method_query = self.language_obj.query(self.query_config['method_query'])
        self.doc_query = self.language_obj.query(self.query_config['doc_query'])

    @staticmethod
    def create_treesitter(language: LanguageEnum) -> "Treesitter":
        """
        Factory method to create a new Treesitter instance.

        Args:
            language (LanguageEnum): The programming language to parse

        Returns:
            Treesitter: A new Treesitter instance configured for the specified language
        """
        return Treesitter(language)

    def parse(self, file_bytes: bytes) -> tuple[list[TreesitterClassNode], list[TreesitterMethodNode]]:
        """
        Parse source code and extract class and method information.

        Args:
            file_bytes (bytes): Source code content as bytes

        Returns:
            tuple[list[TreesitterClassNode], list[TreesitterMethodNode]]: A tuple containing:
                - List of TreesitterClassNode objects representing found classes
                - List of TreesitterMethodNode objects representing found methods
        """
        tree = self.parser.parse(file_bytes)
        root_node = tree.root_node

        class_results = []
        method_results = []

        class_name_by_node = {}
        class_captures = self.class_query.captures(root_node)
        class_nodes = []
        for node, capture_name in class_captures:
            if capture_name == 'class.name':
                class_name = node.text.decode()
                class_node = node.parent
                logging.info(f"Found class: {class_name}")
                class_name_by_node[class_node.id] = class_name
                method_declarations = self._extract_methods_in_class(class_node)
                class_results.append(TreesitterClassNode(class_name, method_declarations, class_node))
                class_nodes.append(class_node)

        method_captures = self.method_query.captures(root_node)
        for node, capture_name in method_captures:
            if capture_name in ['method.name', 'function.name']:
                method_name = node.text.decode()
                method_node = node.parent
                method_source_code = method_node.text.decode()
                doc_comment = self._extract_doc_comment(method_node)
                parent_class_name = None
                for class_node in class_nodes:
                    if self._is_descendant_of(method_node, class_node):
                        parent_class_name = class_name_by_node[class_node.id]
                        break
                method_results.append(TreesitterMethodNode(
                    name=method_name,
                    doc_comment=doc_comment,
                    method_source_code=method_source_code,
                    node=method_node,
                    class_name=parent_class_name
                ))

        return class_results, method_results

    def _extract_methods_in_class(self, class_node):
        """
        Extract method declarations from a class node.

        Args:
            class_node: The tree-sitter node representing a class

        Returns:
            list[str]: List of method declarations found in the class
        """
        method_declarations = []
        # Apply method_query to the class_node
        method_captures = self.method_query.captures(class_node)
        for node, capture_name in method_captures:
            if capture_name in ['method.name', 'function.name']:
                method_declaration = node.parent.text.decode()
                method_declarations.append(method_declaration)
        return method_declarations

    def _extract_doc_comment(self, node):
        """
        Extract documentation comments preceding a node.

        Args:
            node: The tree-sitter node to extract documentation from

        Returns:
            str: The extracted documentation comment, or empty string if none found
        """
        # Search for doc comments preceding the node
        doc_comment = ''
        current_node = node.prev_sibling
        while current_node:
            captures = self.doc_query.captures(current_node)
            if captures:
                for cap_node, cap_name in captures:
                    if cap_name == 'comment':
                        doc_comment = cap_node.text.decode() + '\n' + doc_comment
            elif current_node.type not in ['comment', 'block_comment', 'line_comment', 'expression_statement']:
                # Stop if we reach a node that's not a comment
                break
            current_node = current_node.prev_sibling
        return doc_comment.strip()

    def _is_descendant_of(self, node, ancestor):
        """
        Check if a node is a descendant of another node in the AST.

        Args:
            node: The potential descendant node
            ancestor: The potential ancestor node

        Returns:
            bool: True if node is a descendant of ancestor, False otherwise
        """
        # Check if 'node' is a descendant of 'ancestor'
        current = node.parent
        while current:
            if current == ancestor:
                return True
            current = current.parent
        return False
