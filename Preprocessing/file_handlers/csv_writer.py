import os
import csv
from typing import List, Dict

def create_output_directory(codebase_path: str) -> str:
    normalized_path = os.path.normpath(os.path.abspath(codebase_path))
    codebase_folder_name = os.path.basename(normalized_path)
    output_directory = os.path.join("processed", codebase_folder_name)
    os.makedirs(output_directory, exist_ok=True)
    return output_directory

def write_class_data_to_csv(class_data: List[Dict], output_directory: str) -> None:
    output_file = os.path.join(output_directory, "class_data.csv")
    fieldnames = ["file_path", "class_name", "constructor_declaration", "method_declarations", "source_code", "references"]
    
    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in class_data:
            references = row.get("references", [])
            row["references"] = "; ".join([f"{ref['file']}:{ref['line']}:{ref['column']}" for ref in references])
            writer.writerow(row)
    print(f"Class data written to {output_file}")

def write_method_data_to_csv(method_data: List[Dict], output_directory: str) -> None:
    output_file = os.path.join(output_directory, "method_data.csv")
    fieldnames = ["file_path", "class_name", "name", "doc_comment", "source_code", "references"]
    
    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in method_data:
            references = row.get("references", [])
            row["references"] = "; ".join([f"{ref['file']}:{ref['line']}:{ref['column']}" for ref in references])
            writer.writerow(row)
    print(f"Method data written to {output_file}") 