"""Embedding service for semantic search."""

from typing import List

from langchain_openai import OpenAIEmbeddings

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings.

    Uses OpenAI embeddings for semantic similarity search.
    Can be configured to use different embedding models.
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str = None,
    ) -> None:
        """Initialize embedding service.

        Args:
            model: OpenAI embedding model name
            api_key: OpenAI API key (optional, uses env var if not provided)
        """
        self.model = model
        self.api_key = api_key

        # Initialize OpenAI embeddings
        kwargs = {"model": model}
        if api_key:
            kwargs["openai_api_key"] = api_key

        self.embeddings = OpenAIEmbeddings(**kwargs)

        logger.info("embedding_service_initialized", model=model)

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            # OpenAI embeddings are async-compatible
            embedding = await self.embeddings.aembed_query(text)

            logger.debug(
                "text_embedded",
                text_length=len(text),
                embedding_dim=len(embedding),
            )

            return embedding

        except Exception as e:
            logger.error(
                "embedding_failed",
                text_length=len(text),
                error=str(e),
            )
            raise

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            embeddings = await self.embeddings.aembed_documents(texts)

            logger.info(
                "documents_embedded",
                count=len(texts),
                embedding_dim=len(embeddings[0]) if embeddings else 0,
            )

            return embeddings

        except Exception as e:
            logger.error(
                "batch_embedding_failed",
                count=len(texts),
                error=str(e),
            )
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model.

        Returns:
            Embedding dimension
        """
        # text-embedding-3-small: 1536 dimensions
        # text-embedding-3-large: 3072 dimensions
        # text-embedding-ada-002: 1536 dimensions
        if "large" in self.model:
            return 3072
        return 1536
