from typing import List, Dict, Any, Tuple
import tiktoken
from ..models.legal_schemas import LegalProvision, LegalLevel
from ..models.storage_models import TextChunkSchema


class LegalChunker:
    """Legal-aware text chunking for hierarchical legal documents"""

    def __init__(self, max_chunk_tokens: int = 1024, overlap_tokens: int = 128):
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens
        self.encoder = tiktoken.encoding_for_model("gpt-4o")

    def chunk_legal_document(
        self, provisions: List[LegalProvision], document_id: str
    ) -> Dict[str, TextChunkSchema]:
        """Chunk legal document based on hierarchical structure"""
        chunks = {}

        for provision in provisions:
            # Create chunks based on legal hierarchy
            provision_chunks = self._chunk_provision(provision, document_id)
            chunks.update(provision_chunks)

        return chunks

    def _chunk_provision(
        self, provision: LegalProvision, document_id: str
    ) -> Dict[str, TextChunkSchema]:
        """Chunk a single legal provision"""
        chunks = {}

        # For smaller provisions (Điều, Khoản), keep as single chunk
        if provision.level in [LegalLevel.DIEU, LegalLevel.KHOAN]:
            chunk_id = f"chunk-{provision.id}"
            chunks[chunk_id] = TextChunkSchema(
                id=chunk_id,
                content=provision.content,
                document_id=document_id,
                chunk_order=0,
                token_count=len(self.encoder.encode(provision.content)),
                metadata={
                    "provision_id": provision.id,
                    "level": provision.level.value,
                    "number": provision.number,
                    "title": provision.title,
                    "hierarchy_path": provision.hierarchy_path,
                },
            )
        else:
            # For larger provisions (Phần, Chương, Mục), split if needed
            chunks.update(self._split_large_provision(provision, document_id))

        return chunks

    def _split_large_provision(
        self, provision: LegalProvision, document_id: str
    ) -> Dict[str, TextChunkSchema]:
        """Split large provisions into smaller chunks"""
        chunks = {}
        content = provision.content
        tokens = self.encoder.encode(content)

        if len(tokens) <= self.max_chunk_tokens:
            # Single chunk
            chunk_id = f"chunk-{provision.id}"
            chunks[chunk_id] = TextChunkSchema(
                id=chunk_id,
                content=content,
                document_id=document_id,
                chunk_order=0,
                token_count=len(tokens),
                metadata={
                    "provision_id": provision.id,
                    "level": provision.level.value,
                    "number": provision.number,
                    "title": provision.title,
                    "hierarchy_path": provision.hierarchy_path,
                },
            )
        else:
            # Multiple chunks
            chunk_texts = self._split_text_by_tokens(content, tokens)
            for i, chunk_text in enumerate(chunk_texts):
                chunk_id = f"chunk-{provision.id}-{i}"
                chunks[chunk_id] = TextChunkSchema(
                    id=chunk_id,
                    content=chunk_text,
                    document_id=document_id,
                    chunk_order=i,
                    token_count=len(self.encoder.encode(chunk_text)),
                    metadata={
                        "provision_id": provision.id,
                        "level": provision.level.value,
                        "number": provision.number,
                        "title": provision.title,
                        "hierarchy_path": provision.hierarchy_path,
                        "chunk_part": i,
                    },
                )

        return chunks

    def _split_text_by_tokens(self, text: str, tokens: List[int]) -> List[str]:
        """Split text into chunks based on token limits"""
        chunks = []
        start_idx = 0

        while start_idx < len(tokens):
            end_idx = min(start_idx + self.max_chunk_tokens, len(tokens))

            # Find good break point (sentence boundary)
            if end_idx < len(tokens):
                chunk_tokens = tokens[start_idx:end_idx]
                chunk_text = self.encoder.decode(chunk_tokens)

                # Look for sentence boundaries
                sentences = chunk_text.split(".")
                if len(sentences) > 1:
                    # Keep all but last incomplete sentence
                    good_text = ".".join(sentences[:-1]) + "."
                    chunks.append(good_text)

                    # Recalculate start for next chunk with overlap
                    good_tokens = self.encoder.encode(good_text)
                    start_idx += len(good_tokens) - self.overlap_tokens
                else:
                    chunks.append(chunk_text)
                    start_idx = end_idx - self.overlap_tokens
            else:
                # Last chunk
                chunk_tokens = tokens[start_idx:end_idx]
                chunks.append(self.encoder.decode(chunk_tokens))
                break

        return chunks
