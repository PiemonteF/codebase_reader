import os
from typing import List, Tuple
from Preprocessing.Treesitter.treesitter import LanguageEnum
from Preprocessing.config.constants import (
    BLACKLIST_DIR,
    WHITELIST_FILES,
    BLACKLIST_FILES,
    FILE_EXTENSION_LANGUAGE_MAP
)

def get_language_from_extension(file_ext: str) -> LanguageEnum:
    return FILE_EXTENSION_LANGUAGE_MAP.get(file_ext)

def load_files(codebase_path: str) -> List[Tuple[str, LanguageEnum]]:
    file_list = []
    for root, dirs, files in os.walk(codebase_path):
        dirs[:] = [d for d in dirs if d not in BLACKLIST_DIR]
        for file in files:
            file_ext = os.path.splitext(file)[1]
            if file_ext in WHITELIST_FILES and file not in BLACKLIST_FILES:
                file_path = os.path.join(root, file)
                language = get_language_from_extension(file_ext)
                if language:
                    file_list.append((file_path, language))
                else:
                    print(f"Unsupported file extension {file_ext} in file {file_path}. Skipping.")
    return file_list 