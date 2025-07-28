from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class DatabaseConfig(BaseModel):
    neo4j: Dict[str, Any]
    postgres: Dict[str, Any]
    chromadb: Dict[str, Any]


class LLMConfig(BaseModel):
    openai: Optional[Dict[str, Any]] = None
    gemini: Optional[Dict[str, Any]] = None


class LegalProcessingConfig(BaseModel):
    chunk_strategy: str = "legal_structure"
    max_chunk_tokens: int = 1024
    enable_cross_reference: bool = True
    enable_precedence_analysis: bool = True
    hierarchy_levels: List[str] = Field(
        default_factory=lambda: ["phan", "chuong", "muc", "dieu", "khoan"]
    )
    entity_types: List[str] = Field(
        default_factory=lambda: [
            "legal_concept",
            "legal_principle",
            "legal_entity",
            "legal_procedure",
            "legal_provision",
        ]
    )


class HiRAGConfig(BaseModel):
    working_dir: str = "./data/knowledge_base"
    enable_llm_cache: bool = True
    enable_hierarchical_mode: bool = True
    embedding_batch_num: int = 6
    embedding_func_max_async: int = 8
    enable_naive_rag: bool = True


class LegalConfig(BaseModel):
    databases: DatabaseConfig
    llm: LLMConfig
    legal_processing: LegalProcessingConfig
    hirag: HiRAGConfig
