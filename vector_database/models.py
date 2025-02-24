from lancedb.pydantic import LanceModel, Vector
from .config import EMBEDDING_DIM, model

class Method(LanceModel):
    code: str = model.SourceField()
    method_embeddings: Vector(EMBEDDING_DIM) = model.VectorField()
    file_path: str
    class_name: str
    name: str
    doc_comment: str
    source_code: str
    references: str

class Class(LanceModel):
    source_code: str = model.SourceField()
    class_embeddings: Vector(EMBEDDING_DIM) = model.VectorField()
    file_path: str
    class_name: str
    constructor_declaration: str
    method_declarations: str
    references: str 