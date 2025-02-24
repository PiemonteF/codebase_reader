from Preprocessing.Treesitter.treesitter import LanguageEnum

BLACKLIST_DIR = [
    "__pycache__", ".pytest_cache", ".venv", ".git", ".idea",
    "venv", "env", "node_modules", "dist", "build", ".vscode",
    ".github", ".gitlab", ".angular", "cdk.out", ".aws-sam", ".terraform"
]

WHITELIST_FILES = [".py"]
BLACKLIST_FILES = ["docker-compose.yml"]

NODE_TYPES = {
    "python": {
        "class": "class_definition",
        "method": "function_definition"
    },
}

REFERENCE_IDENTIFIERS = {
    "python": {
        "class": "identifier",
        "method": "call",
        "child_field_name": "function"
    },
}

FILE_EXTENSION_LANGUAGE_MAP = {
    ".py": LanguageEnum.PYTHON,
} 