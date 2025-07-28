from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from .legal_schemas import LegalLevel, LegalEntityType


class LegalQueryMode(str, Enum):
    HIERARCHICAL = "hierarchical"  # Full hierarchical context
    LOCAL = "local"  # Local entities & relationships
    GLOBAL = "global"  # Community reports & background
    BRIDGE = "bridge"  # Reasoning paths between entities
    PROVISION = "provision"  # Specific provision lookup
    CROSS_REFERENCE = "cross_reference"  # Cross-reference analysis


class LegalQueryParam(BaseModel):
    mode: LegalQueryMode = LegalQueryMode.HIERARCHICAL
    top_k: int = 20
    max_token_for_context: int = 12000
    include_cross_references: bool = True
    include_hierarchy_context: bool = True
    provision_level_filter: Optional[List[LegalLevel]] = (
        None  # Có thể filter theo 'muc'
    )
    entity_type_filter: Optional[List[LegalEntityType]] = None
    document_filter: Optional[List[str]] = None
    response_type: str = "Multiple Paragraphs"


class LegalQueryResult(BaseModel):
    query: str
    answer: str
    mode: LegalQueryMode
    context_used: Dict[str, Any]
    entities_retrieved: List[Dict[str, Any]] = Field(default_factory=list)
    provisions_referenced: List[str] = Field(default_factory=list)
    cross_references: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    sources: List[Dict[str, str]] = Field(default_factory=list)
    hierarchy_context: Dict[str, Any] = Field(
        default_factory=dict
    )  # Thêm context hierarchy
