import os

def get_name_and_input_dir(codebase_path):
    normalized_path = os.path.normpath(os.path.abspath(codebase_path))
    codebase_folder_name = os.path.basename(normalized_path)
    
    print("codebase_folder_name:", codebase_folder_name)
    
    output_directory = os.path.join("processed", codebase_folder_name)
    os.makedirs(output_directory, exist_ok=True)
    
    return codebase_folder_name, output_directory

def get_special_files(directory):
    md_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.md', '.sh')):
                full_path = os.path.join(root, file)
                md_files.append(full_path)
    return md_files

def process_special_files(md_files):
    contents = {}
    for file_path in md_files:
        with open(file_path, 'r', encoding='utf-8') as file:
            contents[file_path] = file.read()
    return contents 