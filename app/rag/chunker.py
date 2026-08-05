from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    """A deterministic text chunk and its position in the source document."""

    index: int
    content: str


class TextChunker:
    """Split normalized text into overlapping, whitespace-aware character chunks."""

    def __init__(self, chunk_size: int = 1_000, chunk_overlap: int = 200) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[TextChunk]:
        """Return deterministic chunks while retaining a small overlap between chunks."""
        chunks: list[TextChunk] = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                boundary = text.rfind(" ", start + self.chunk_size // 2, end)
                if boundary > start:
                    end = boundary

            content = text[start:end].strip()
            if content:
                chunks.append(TextChunk(index=len(chunks), content=content))

            if end >= len(text):
                break
            start = max(end - self.chunk_overlap, start + 1)

        return chunks
