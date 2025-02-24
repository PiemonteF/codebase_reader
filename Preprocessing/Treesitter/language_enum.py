from enum import Enum

class LanguageEnum(Enum):
    PYTHON = "python"
    UNKNOWN = "unknown"

LANGUAGE_QUERIES = {
    LanguageEnum.PYTHON: {
        'class_query': """
            (class_definition
                name: (identifier) @class.name)
        """,
        'method_query': """
            (function_definition
                name: (identifier) @function.name)
        """,
        'doc_query': """
            (expression_statement
                (string) @comment)
        """,
        'import_query': """
            (import_statement
                name: (dotted_name) @import.name)
            (import_from_statement
                module_name: (dotted_name) @import.from
                name: (dotted_name) @import.name)
        """,
        'variable_query': """
            (assignment
                left: (identifier) @variable.name)
        """
    },
    # Add other languages as needed
} 