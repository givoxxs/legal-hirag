import numpy as np
from typing import List, Dict, Any, Optional
import asyncio
from openai import AsyncOpenAI
import tiktoken


class LegalEmbeddingFunction:
    """Legal-specific embedding function for Vietnamese legal texts"""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-large",
        max_tokens: int = 8192,
        embedding_dim: int = 3072,
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.embedding_dim = embedding_dim
        self.encoder = tiktoken.encoding_for_model("gpt-4o")

    async def __call__(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for legal texts"""
        if not texts:
            return np.array([])

        # Preprocess legal texts
        processed_texts = [self._preprocess_legal_text(text) for text in texts]

        # Batch processing for efficiency
        embeddings = []
        batch_size = 100

        for i in range(0, len(processed_texts), batch_size):
            batch = processed_texts[i : i + batch_size]
            batch_embeddings = await self._get_batch_embeddings(batch)
            embeddings.extend(batch_embeddings)

        return np.array(embeddings)

    def _preprocess_legal_text(self, text: str) -> str:
        """Preprocess Vietnamese legal text for better embeddings"""
        # Remove excessive whitespace
        text = " ".join(text.split())

        # Truncate if too long
        tokens = self.encoder.encode(text)
        if len(tokens) > self.max_tokens:
            tokens = tokens[: self.max_tokens]
            text = self.encoder.decode(tokens)

        return text

    async def _get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts"""
        try:
            response = await self.client.embeddings.create(
                model=self.model, input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Error getting embeddings: {e}")
            # Return zero embeddings as fallback
            return [[0.0] * self.embedding_dim for _ in texts]


class GeminiEmbeddingFunction:
    """Gemini embedding function for legal texts"""

    def __init__(
        self, api_key: str, model: str = "text-embedding-004", embedding_dim: int = 768
    ):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self.model = model
        self.embedding_dim = embedding_dim
        self.genai = genai

    async def __call__(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using Gemini"""
        if not texts:
            return np.array([])

        embeddings = []
        for text in texts:
            try:
                result = self.genai.embed_content(
                    model=self.model, content=text, task_type="retrieval_document"
                )
                embeddings.append(result["embedding"])
            except Exception as e:
                print(f"Error with Gemini embedding: {e}")
                embeddings.append([0.0] * self.embedding_dim)

        return np.array(embeddings)
