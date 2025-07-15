"""
Document embedding generation for vector search.
This module is responsible for converting text chunks into vector embeddings.
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime
import os

from dotenv import load_dotenv

from .chunker import DocumentChunk

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates embeddings for document chunks using a configured provider.
    """

    def __init__(
        self, batch_size: int = 100, max_retries: int = 3, retry_delay: float = 1.0
    ):
        """
        Initialize embedding generator.

        Args:
            batch_size: Number of texts to process in parallel.
            max_retries: Maximum number of retry attempts for failed API calls.
            retry_delay: Delay between retries in seconds.
        """

        from .providers import get_embedder

        self.provider = get_embedder()
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.dimension = self.provider.get_embedding_dimension()

        logger.info(
            f"EmbeddingGenerator initialized with provider: {self.provider.__class__.__name__} "
            f"and dimension: {self.dimension}"
        )

    async def embed_chunks(
        self, chunks: List[DocumentChunk], progress_callback: Optional[callable] = None
    ) -> List[DocumentChunk]:
        """
        Generate and attach embeddings to a list of document chunks.

        Args:
            chunks: List of document chunks to embed.
            progress_callback: Optional callback for progress updates.

        Returns:
            The same list of chunks with the `embedding` attribute populated.
        """
        if not chunks:
            return []

        logger.info(f"Generating embeddings for {len(chunks)} chunks...")

        total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(chunks), self.batch_size):
            batch_chunks = chunks[i : i + self.batch_size]
            batch_texts = [chunk.content for chunk in batch_chunks]

            current_batch_num = (i // self.batch_size) + 1
            logger.info(f"Processing batch {current_batch_num}/{total_batches}")

            for attempt in range(self.max_retries):
                try:
                    embeddings = await self.provider.generate_embeddings_batch(
                        batch_texts
                    )

                    # Attach embeddings to their corresponding chunks
                    for chunk, embedding in zip(batch_chunks, embeddings):
                        chunk.embedding = embedding
                        chunk.metadata["embedding_model"] = os.getenv("EMBEDDING_MODEL")
                        chunk.metadata["embedding_generated_at"] = (
                            datetime.now().isoformat()
                        )

                    if progress_callback:
                        progress_callback(current_batch_num, total_batches)

                    break  # Success, exit retry loop

                except Exception as e:
                    logger.error(
                        f"Failed to process batch {current_batch_num} on attempt {attempt + 1}: {e}"
                    )
                    if attempt == self.max_retries - 1:
                        logger.error(
                            f"Batch {current_batch_num} failed after all retries. Filling with zero vectors."
                        )
                        # Fallback: fill with zero vectors on permanent failure
                        for chunk in batch_chunks:
                            chunk.embedding = [0.0] * self.dimension
                            chunk.metadata["embedding_error"] = str(e)
                    else:
                        delay = self.retry_delay * (2**attempt)
                        logger.info(f"Retrying batch in {delay:.2f} seconds...")
                        await asyncio.sleep(delay)

        logger.info(f"Finished generating embeddings for {len(chunks)} chunks.")
        return chunks

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate an embedding for a single search query.

        Args:
            query: The search query text.

        Returns:
            The embedding vector for the query.
        """
        return await self.provider.generate_embedding(query)

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings for the configured model.

        Returns:
            The vector dimension size.
        """
        return self.dimension


def create_embedder(**kwargs) -> EmbeddingGenerator:
    """
    Factory function to create an instance of the EmbeddingGenerator.

    Args:
        **kwargs: Arguments to pass to the EmbeddingGenerator constructor.

    Returns:
        An instance of EmbeddingGenerator.
    """
    return EmbeddingGenerator(**kwargs)


# Example usage
async def main():
    """Example usage of the embedder."""
    from .chunker import ChunkingConfig, create_chunker

    # Create chunker and embedder
    config = ChunkingConfig(chunk_size=200, use_semantic_splitting=False)
    chunker = create_chunker(config)
    embedder = create_embedder()

    sample_text = """
    Google's AI initiatives include advanced language models.
    Microsoft's partnership with OpenAI has led to GPT integration.
    """

    chunks = chunker.chunk_document(
        content=sample_text, title="AI Initiatives", source="example.md"
    )

    print(f"Created {len(chunks)} chunks.")

    def progress_callback(current, total):
        print(f"Processing batch {current}/{total}")

    embedded_chunks = await embedder.embed_chunks(chunks, progress_callback)

    for i, chunk in enumerate(embedded_chunks):
        embedding_preview = chunk.embedding[:5] if chunk.embedding else None
        print(
            f"Chunk {i}: {len(chunk.content)} chars, embedding dim: {len(chunk.embedding)}, preview: {embedding_preview}..."
        )

    query_embedding = await embedder.embed_query("Google AI research")
    print(f"Query embedding dimension: {len(query_embedding)}")


if __name__ == "__main__":
    asyncio.run(main())
