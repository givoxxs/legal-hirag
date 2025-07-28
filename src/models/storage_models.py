from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class TextChunkSchema(BaseModel):
    """Schema for text chunks storage"""

    id: str
    content: str
    document_id: str
    chunk_order: int = 0
    token_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class CommunitySchema(BaseModel):
    """Schema for community reports storage"""

    id: str
    level: int
    title: str
    summary: str
    report_string: str
    report_json: Dict[str, Any]
    entity_count: int = 0
    relationship_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class SingleCommunitySchema(BaseModel):
    """Schema for single community data"""

    id: str
    level: int
    entities: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)
    sub_communities: List[str] = Field(default_factory=list)


class QueryParam(BaseModel):
    """Query parameters for legal queries"""

    mode: str = "hierarchical"
    top_k: int = 20
    max_token_for_context: int = 12000
    max_token_for_community_report: int = 8000
    level: int = 2
    response_type: str = "Multiple Paragraphs"
    only_need_context: bool = False
    community_single_one: bool = False
