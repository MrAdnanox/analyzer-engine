# FICHIER: analyzer-engine/ingestion/chunker.py (VERSION SYNTAXIQUEMENT PARFAITE)
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio
import os

from dotenv import load_dotenv

from core.contracts.provider_contracts import LLMProvider
from core.models.db import IngestionConfig

load_dotenv()
logger = logging.getLogger(__name__)

# L'initialisation précoce au niveau du module a été supprimée. C'est correct.


@dataclass
class DocumentChunk:
    content: str
    index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]
    token_count: Optional[int] = None
    embedding: Optional[List[float]] = None

    def __post_init__(self):
        if self.token_count is None:
            self.token_count = len(self.content) // 4


class SemanticChunker:
    def __init__(self, config: IngestionConfig, llm_provider: LLMProvider):
        self.config = config
        self.model = llm_provider

    def chunk_from_entities(
        self,
        entities: List[Dict[str, Any]],
        file_path: str,
        base_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        chunk_objects = []
        if not base_metadata:
            base_metadata = {}
        for i, entity in enumerate(entities):
            if not entity.get("source_code"):
                continue
            chunk_metadata = {
                **base_metadata,
                "entity_name": entity.get("name"),
                "entity_type": entity.get("type"),
                "file_path": file_path,
                "chunk_method": "entity_based",
            }
            chunk_objects.append(
                DocumentChunk(
                    content=entity["source_code"],
                    index=i,
                    start_char=0,
                    end_char=len(entity["source_code"]),
                    metadata=chunk_metadata,
                )
            )
        return chunk_objects

    async def chunk_document(
        self,
        content: str,
        title: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        if not content.strip():
            return []
        base_metadata = {"title": title, "source": source, **(metadata or {})}
        if self.config.use_semantic_chunking and len(content) > self.config.chunk_size:
            try:
                semantic_chunks = await self._semantic_chunk(content)
                if semantic_chunks:
                    return self._create_chunk_objects(
                        semantic_chunks, content, base_metadata
                    )
            except Exception as e:
                logger.warning(
                    f"Semantic chunking failed, falling back to simple chunking: {e}"
                )
        return self._simple_chunk(content, base_metadata)

    async def _semantic_chunk(self, content: str) -> List[str]:
        sections = self._split_on_structure(content)
        chunks, current_chunk = [], ""
        for section in sections:
            potential_chunk = (
                current_chunk + "\n\n" + section if current_chunk else section
            )
            if len(potential_chunk) <= self.config.chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                if len(section) > self.config.max_chunk_size:
                    chunks.extend(await self._split_long_section(section))
                else:
                    current_chunk = section
        if current_chunk:
            chunks.append(current_chunk.strip())
        return [
            chunk
            for chunk in chunks
            if len(chunk.strip()) >= self.config.min_chunk_size
        ]

    def _split_on_structure(self, content: str) -> List[str]:
        patterns = [
            r"\n#{1,6}\s+.+?\n",
            r"\n\n+",
            r"\n[-*+]\s+",
            r"\n\d+\.\s+",
            r"\n```.*?```\n",
            r"\n\|\s*.+?\|\s*\n",
        ]
        sections = [content]
        for pattern in patterns:
            new_sections = []
            for section in sections:
                new_sections.extend(
                    [
                        part
                        for part in re.split(
                            f"({pattern})", section, flags=re.MULTILINE | re.DOTALL
                        )
                        if part.strip()
                    ]
                )
            sections = new_sections
        return sections

    async def _split_long_section(self, section: str) -> List[str]:
        try:
            prompt = f"Split the following text into semantically coherent chunks...\nText to split:\n{section}"
            response = await self.model.generate_text(prompt)
            chunks = [chunk.strip() for chunk in response.split("---CHUNK---")]
            valid_chunks = [
                chunk
                for chunk in chunks
                if self.config.min_chunk_size
                <= len(chunk)
                <= self.config.max_chunk_size
            ]
            return valid_chunks if valid_chunks else self._simple_split(section)
        except Exception as e:
            logger.error(f"LLM chunking failed: {e}")
            return self._simple_split(section)

    def _simple_split(self, text: str) -> List[str]:
        chunks, start = [], 0
        while start < len(text):
            end = start + self.config.chunk_size
            if end >= len(text):
                chunks.append(text[start:])
                break
            chunk_end = end
            for i in range(end, max(start + self.config.min_chunk_size, end - 200), -1):
                if text[i] in ".!?\n":
                    chunk_end = i + 1
                    break
            chunks.append(text[start:chunk_end])
            start = chunk_end - self.config.chunk_overlap
        return chunks

    def _simple_chunk(
        self, content: str, base_metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        chunks = self._simple_split(content)
        return self._create_chunk_objects(chunks, content, base_metadata)

    def _create_chunk_objects(
        self, chunks: List[str], original_content: str, base_metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        chunk_objects, current_pos = [], 0
        for i, chunk_text in enumerate(chunks):
            start_pos = original_content.find(chunk_text, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(chunk_text)
            chunk_metadata = {
                **base_metadata,
                "chunk_method": (
                    "semantic" if self.config.use_semantic_chunking else "simple"
                ),
                "total_chunks": len(chunks),
            }
            chunk_objects.append(
                DocumentChunk(
                    content=chunk_text.strip(),
                    index=i,
                    start_char=start_pos,
                    end_char=end_pos,
                    metadata=chunk_metadata,
                )
            )
            current_pos = end_pos
        return chunk_objects


class SimpleChunker:
    def __init__(self, config: IngestionConfig):
        self.config = config

    def chunk_from_entities(
        self,
        entities: List[Dict[str, Any]],
        file_path: str,
        base_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        chunk_objects = []
        if not base_metadata:
            base_metadata = {}
        for i, entity in enumerate(entities):
            if not entity.get("source_code"):
                continue
            chunk_metadata = {
                **base_metadata,
                "entity_name": entity.get("name"),
                "entity_type": entity.get("type"),
                "file_path": file_path,
                "chunk_method": "entity_based",
            }
            chunk_objects.append(
                DocumentChunk(
                    content=entity["source_code"],
                    index=i,
                    start_char=0,
                    end_char=len(entity["source_code"]),
                    metadata=chunk_metadata,
                )
            )
        return chunk_objects

    def chunk_document(
        self,
        content: str,
        title: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        if not content.strip():
            return []
        base_metadata = {
            "title": title,
            "source": source,
            "chunk_method": "simple",
            **(metadata or {}),
        }
        paragraphs = re.split(r"\n\s*\n", content)
        chunks, current_chunk, current_pos, chunk_index = [], "", 0, 0
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            potential_chunk = (
                current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            )
            if len(potential_chunk) <= self.config.chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(
                        self._create_chunk(
                            current_chunk,
                            chunk_index,
                            current_pos,
                            current_pos + len(current_chunk),
                            base_metadata.copy(),
                        )
                    )
                    current_pos += max(
                        0, len(current_chunk) - self.config.chunk_overlap
                    )
                    chunk_index += 1
                current_chunk = paragraph
        if current_chunk:
            chunks.append(
                self._create_chunk(
                    current_chunk,
                    chunk_index,
                    current_pos,
                    current_pos + len(current_chunk),
                    base_metadata.copy(),
                )
            )
        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)
        return chunks

    def _create_chunk(
        self,
        content: str,
        index: int,
        start_pos: int,
        end_pos: int,
        metadata: Dict[str, Any],
    ) -> DocumentChunk:
        return DocumentChunk(
            content=content.strip(),
            index=index,
            start_char=start_pos,
            end_char=end_pos,
            metadata=metadata,
        )


def create_chunker(config: IngestionConfig):
    """Factory qui instancie et injecte les dépendances."""
    if config.use_semantic_chunking:
        from .providers import get_ingestion_model

        llm_provider = get_ingestion_model()
        if llm_provider is None:
            raise RuntimeError(
                "LLM Provider could not be initialized. Check INGESTION_LLM_CHOICE env var."
            )
        return SemanticChunker(config, llm_provider=llm_provider)
    else:
        return SimpleChunker(config)


async def main():
    config = IngestionConfig(
        chunk_size=500, chunk_overlap=50, use_semantic_chunking=True
    )
    os.environ["INGESTION_LLM_CHOICE"] = "gemini-1.5-flash"
    chunker = create_chunker(config)
    sample_text = "# Title\n\nContent..."
    chunks = await chunker.chunk_document(
        content=sample_text, title="Test", source="test.md"
    )
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: {chunk.content[:50]}...")


if __name__ == "__main__":
    asyncio.run(main())
