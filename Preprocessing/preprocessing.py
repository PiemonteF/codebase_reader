import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from Preprocessing.file_handlers.file_loader import load_files
from Preprocessing.file_handlers.csv_writer import (
    create_output_directory,
    write_class_data_to_csv,
    write_method_data_to_csv
)
from Preprocessing.Treesitter.treesitter import Treesitter

def parse_code_files(file_list):
    """
    Parse source code files to extract class and method information.

    Args:
        file_list: List of tuples containing (file_path, language) pairs

    Returns:
        tuple: Contains:
            - class_data (list): List of dictionaries containing class information
            - method_data (list): List of dictionaries containing method information
            - all_class_names (set): Set of all class names found
            - all_method_names (set): Set of all method names found
    """
    class_data = []
    method_data = []

    all_class_names = set()
    all_method_names = set()

    files_by_language = defaultdict(list)
    for file_path, language in file_list:
        files_by_language[language].append(file_path)

    for language, files in files_by_language.items():
        treesitter_parser = Treesitter.create_treesitter(language)
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as file:
                code = file.read()
                file_bytes = code.encode()
                class_nodes, method_nodes = treesitter_parser.parse(file_bytes)

                # Process class nodes
                for class_node in class_nodes:
                    class_name = class_node.name
                    all_class_names.add(class_name)
                    class_data.append({
                        "file_path": file_path,
                        "class_name": class_name,
                        "constructor_declaration": "",  # Extract if needed
                        "method_declarations": "\n-----\n".join(class_node.method_declarations) if class_node.method_declarations else "",
                        "source_code": class_node.source_code,
                        "references": []  # Will populate later
                    })

                # Process method nodes
                for method_node in method_nodes:
                    method_name = method_node.name
                    all_method_names.add(method_name)
                    method_data.append({
                        "file_path": file_path,
                        "class_name": method_node.class_name if method_node.class_name else "",
                        "name": method_name,
                        "doc_comment": method_node.doc_comment,
                        "source_code": method_node.method_source_code,
                        "references": []  # Will populate later
                    })

    return class_data, method_data, all_class_names, all_method_names

def find_references(file_list, class_names, method_names):
    """
    Find all references to classes and methods within the codebase.

    Args:
        file_list: List of tuples containing (file_path, language) pairs
        class_names: Collection of class names to search for
        method_names: Collection of method names to search for

    Returns:
        dict: Dictionary containing two defaultdict(list) objects:
            - 'class': Maps class names to lists of reference information
            - 'method': Maps method names to lists of reference information
            Each reference contains file path, line number, column number, and context
    """
    references = {'class': defaultdict(list), 'method': defaultdict(list)}
    files_by_language = defaultdict(list)
    
    # Convert names to sets for O(1) lookup
    class_names = set(class_names)
    method_names = set(method_names)

    for file_path, language in file_list:
        files_by_language[language].append(file_path)

    for language, files in files_by_language.items():
        treesitter_parser = Treesitter.create_treesitter(language)
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as file:
                code = file.read()
                file_bytes = code.encode()
                tree = treesitter_parser.parser.parse(file_bytes)
                
                # Single pass through the AST
                stack = [(tree.root_node, None)]
                while stack:
                    node, parent = stack.pop()
                    
                    # Check for identifiers
                    if node.type == 'identifier':
                        name = node.text.decode()
                        
                        # Check if it's a class reference
                        if name in class_names and parent and parent.type in ['type', 'class_type', 'object_creation_expression']:
                            references['class'][name].append({
                                "file": file_path,
                                "line": node.start_point[0] + 1,
                                "column": node.start_point[1] + 1,
                                "text": parent.text.decode()
                            })
                        
                        # Check if it's a method reference
                        if name in method_names and parent and parent.type in ['call_expression', 'method_invocation']:
                            references['method'][name].append({
                                "file": file_path,
                                "line": node.start_point[0] + 1,
                                "column": node.start_point[1] + 1,
                                "text": parent.text.decode()
                            })
                    
                    # Add children to stack with their parent
                    stack.extend((child, node) for child in node.children)

    return references

def main(codebase_path: str) -> None:
    """
    Main function to process a codebase and generate analysis CSV files.

    Args:
        codebase_path (str): Path to the root directory of the codebase to analyze

    Returns:
        None: Writes results to CSV files in an output directory
    """
    files = load_files(codebase_path)
    class_data, method_data, class_names, method_names = parse_code_files(files)

    # Find references
    references = find_references(files, class_names, method_names)

    # Map references back to class and method data
    class_data_dict = {cd['class_name']: cd for cd in class_data}
    method_data_dict = {(md['class_name'], md['name']): md for md in method_data}

    for class_name, refs in references['class'].items():
        if class_name in class_data_dict:
            class_data_dict[class_name]['references'] = refs

    for method_name, refs in references['method'].items():
        for key in method_data_dict:
            if key[1] == method_name:
                method_data_dict[key]['references'] = refs

    # Convert dictionaries back to lists
    class_data = list(class_data_dict.values())
    method_data = list(method_data_dict.values())

    output_directory = create_output_directory(codebase_path)
    write_class_data_to_csv(class_data, output_directory)
    write_method_data_to_csv(method_data, output_directory)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the codebase path as an argument.")
        sys.exit(1)
    main(sys.argv[1])
