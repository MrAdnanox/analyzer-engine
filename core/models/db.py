# NOUVEAU FICHIER: analyzer-engine/core/models/db.py
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional
from datetime import datetime

class DocumentMetadata(BaseModel):
    id: str
    title: str
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    chunk_count: Optional[int] = None

class ChunkResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_title: str
    document_source: str

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

class GraphSearchResult(BaseModel):
    fact: str
    uuid: str
    valid_at: Optional[str] = None
    invalid_at: Optional[str] = None
    source_node_uuid: Optional[str] = None

class IngestionConfig(BaseModel):
    """Configuration for document ingestion."""
    chunk_size: int = Field(default=1000, ge=100, le=5000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    max_chunk_size: int = Field(default=2000, ge=500, le=10000)
    min_chunk_size: int = Field(default=100, ge=1, description="Minimum size for a chunk in characters")
    use_semantic_chunking: bool = True
    extract_entities: bool = True
    # New option for faster ingestion
    skip_graph_building: bool = Field(default=False, description="Skip knowledge graph building for faster ingestion")
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """Ensure overlap is less than chunk size."""
        chunk_size = info.data.get('chunk_size', 1000)
        if v >= chunk_size:
            raise ValueError(f"Chunk overlap ({v}) must be less than chunk size ({chunk_size})")
        return v