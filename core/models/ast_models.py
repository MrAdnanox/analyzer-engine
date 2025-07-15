from pydantic import BaseModel
from typing import List, Dict, Any

class ASTNode(BaseModel):
    node_type: str
    name: str
    children: List['ASTNode'] = []
    metadata: Dict[str, Any] = {}

class NormalizedAST(BaseModel):
    root: ASTNode
    language: str