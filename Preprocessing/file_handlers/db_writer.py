import sqlite3
from typing import List, Dict, Any
import logging
from dataclasses import dataclass
from pathlib import Path

@dataclass
class FileInfo:
    filepath: str
    module_docstring: str

@dataclass
class Dependency:
    file_id: int
    name: str
    line: int

@dataclass
class ClassInfo:
    file_id: int
    name: str
    line: int
    docstring: str

@dataclass
class FunctionInfo:
    file_id: int
    name: str
    line: int
    docstring: str
    class_name: str = None

@dataclass
class VariableInfo:
    file_id: int
    name: str
    line: int

class DatabaseWriter:
    def __init__(self, db_path: str = "processed/codebase.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Create files table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE NOT NULL,
                module_docstring TEXT
            )
        """)

        # Create dependencies table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                name TEXT NOT NULL,
                line INTEGER NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        """)

        # Create classes table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                name TEXT NOT NULL,
                line INTEGER NOT NULL,
                docstring TEXT,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        """)

        # Create functions table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS functions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                name TEXT NOT NULL,
                line INTEGER NOT NULL,
                docstring TEXT,
                class_name TEXT,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        """)

        # Create variables table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS variables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                name TEXT NOT NULL,
                line INTEGER NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        """)
        
        self.conn.commit()

    def add_file(self, file_info: FileInfo) -> int:
        self.cursor.execute(
            "INSERT INTO files (filepath, module_docstring) VALUES (?, ?)",
            (file_info.filepath, file_info.module_docstring)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def add_dependency(self, dependency: Dependency):
        self.cursor.execute(
            "INSERT INTO dependencies (file_id, name, line) VALUES (?, ?, ?)",
            (dependency.file_id, dependency.name, dependency.line)
        )
        self.conn.commit()

    def add_class(self, class_info: ClassInfo):
        self.cursor.execute(
            "INSERT INTO classes (file_id, name, line, docstring) VALUES (?, ?, ?, ?)",
            (class_info.file_id, class_info.name, class_info.line, class_info.docstring)
        )
        self.conn.commit()

    def add_function(self, function_info: FunctionInfo):
        self.cursor.execute(
            "INSERT INTO functions (file_id, name, line, docstring, class_name) VALUES (?, ?, ?, ?, ?)",
            (function_info.file_id, function_info.name, function_info.line, 
             function_info.docstring, function_info.class_name)
        )
        self.conn.commit()

    def add_variable(self, variable_info: VariableInfo):
        self.cursor.execute(
            "INSERT INTO variables (file_id, name, line) VALUES (?, ?, ?)",
            (variable_info.file_id, variable_info.name, variable_info.line)
        )
        self.conn.commit()

    def close(self):
        self.conn.close() 