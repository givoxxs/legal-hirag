from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class LegalLevel(str, Enum):
    PHAN = "phan"
    CHUONG = "chuong"
    MUC = "muc"
    DIEU = "dieu"
    KHOAN = "khoan"


class LegalEntityType(str, Enum):
    LEGAL_CONCEPT = "legal_concept"  # Khái niệm pháp lý
    LEGAL_PRINCIPLE = "legal_principle"  # Nguyên tắc pháp lý
    LEGAL_ENTITY = "legal_entity"  # Chủ thể pháp lý
    LEGAL_PROCEDURE = "legal_procedure"  # Thủ tục pháp lý
    LEGAL_PROVISION = "legal_provision"  # Điều khoản pháp luật


class LegalRelationType(str, Enum):
    CONTAINS = "CONTAINS"  # Phân cấp
    REFERENCES = "REFERENCES"  # Tham chiếu
    DEFINES = "DEFINES"  # Định nghĩa
    REGULATES = "REGULATES"  # Điều chỉnh
    RELATES_TO = "RELATES_TO"  # Liên quan
    SUPERSEDES = "SUPERSEDES"  # Thay thế
    AMENDS = "AMENDS"  # Sửa đổi


class LegalProvision(BaseModel):
    id: str
    level: LegalLevel
    number: str
    title: Optional[str] = None
    content: str
    document_id: str
    parent_id: Optional[str] = None
    hierarchy_path: List[str] = Field(default_factory=list)
    cross_references: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class LegalEntity(BaseModel):
    name: str
    type: LegalEntityType
    description: str
    level: Optional[LegalLevel] = None
    source_id: str
    confidence_score: Optional[float] = None
    synonyms: List[str] = Field(default_factory=list)
    related_provisions: List[str] = Field(default_factory=list)


class LegalRelationship(BaseModel):
    source_entity: str
    target_entity: str
    relation_type: LegalRelationType
    description: str
    strength: float
    source_id: str
    bidirectional: bool = False


class LegalDocument(BaseModel):
    id: str
    title: str
    document_type: str
    source_file: Optional[str] = None
    structure: Dict[str, Any]
    provisions: List[LegalProvision] = Field(default_factory=list)
    entities: List[LegalEntity] = Field(default_factory=list)
    relationships: List[LegalRelationship] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
