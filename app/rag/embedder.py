import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from app.core.exceptions import ServiceUnavailableError

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
logger: logging.Logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder:
    """Generate normalized embeddings with the configured MiniLM model."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self.model: Any = SentenceTransformer(model_name)
        except Exception as exc:
            logger.exception("Embedding model initialization failed model=%s", model_name)
            raise ServiceUnavailableError("Embedding model") from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a non-empty list of texts and return plain Python float lists."""
        if not texts:
            return []

        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except Exception as exc:
            logger.exception("Embedding generation failed")
            raise ServiceUnavailableError("Embedding model") from exc
        return embeddings.tolist()


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformerEmbedder:
    """Load the embedding model once per application process."""
    return SentenceTransformerEmbedder()
