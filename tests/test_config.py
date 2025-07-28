# tests/test_config.py
import pytest
import os
import tempfile
from src.legal_hirag.models.config_models import LegalConfig
from src.legal_hirag.utils.config_loader import ConfigLoader


def test_config_loading():
    """Test configuration loading from YAML"""
    config_content = """  
databases:  
  neo4j:  
    uri: "bolt://localhost:7687"  
    user: "neo4j"  
    password: "password"  
  postgres:  
    host: "localhost"  
    port: 5432  
    database: "test_db"  
    user: "test_user"  
    password: "test_password"  
  chromadb:  
    persist_directory: "./test_chroma"  
    collection_name: "test_collection"  
  
llm:  
  openai:  
    api_key: "test_key"  
    base_url: "https://api.openai.com/v1"  
    model: "gpt-4o"  
    embedding_model: "text-embedding-3-large"  
    embedding_dim: 3072  
    max_token_size: 8192  
  glm:  
    api_key: "test_glm_key"  
    base_url: "https://test.com"  
    model: "glm-4-plus"  
    embedding_model: "embedding-3"  
    embedding_dim: 2048  
  
legal_processing:  
  chunk_strategy: "legal_structure"  
  max_chunk_tokens: 1024  
  enable_cross_reference: true  
  enable_precedence_analysis: true  
  entity_types:  
    - "legal_provision"  
    - "legal_concept"  
  
hirag:  
  working_dir: "./test_working"  
  enable_llm_cache: true  
  enable_hierarchical_mode: true  
  embedding_batch_num: 6  
  embedding_func_max_async: 8  
  enable_naive_rag: true  
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        config_path = f.name

    try:
        config = ConfigLoader.load_config(config_path)
        assert isinstance(config, LegalConfig)
        assert config.databases.neo4j["uri"] == "bolt://localhost:7687"
        assert config.legal_processing.chunk_strategy == "legal_structure"
        assert len(config.legal_processing.entity_types) == 2
    finally:
        os.unlink(config_path)


def test_legal_schemas():
    """Test legal schema models"""
    from src.legal_hirag.models.legal_schemas import (
        LegalLevel,
        LegalEntityType,
        LegalChunk,
        LegalMetadata,
    )

    # Test enum values
    assert LegalLevel.DIEU == "dieu"
    assert LegalEntityType.LEGAL_PROVISION == "legal_provision"

    # Test metadata creation
    metadata = LegalMetadata(
        level=LegalLevel.DIEU,
        number="1",
        title="Phạm vi điều chỉnh",
        hierarchy_path=["chuong-1", "dieu-1"],
    )

    assert metadata.level == LegalLevel.DIEU
    assert metadata.number == "1"
    assert len(metadata.hierarchy_path) == 2


def test_validation():
    """Test validation utilities"""
    from src.legal_hirag.utils.validation import LegalTextValidator, LegalDataValidator

    validator = LegalTextValidator()

    # Test legal provision validation
    assert validator.validate_legal_provision("Điều 1. Phạm vi điều chỉnh")
    assert validator.validate_legal_provision("CHƯƠNG I: QUY ĐỊNH CHUNG")
    assert not validator.validate_legal_provision("This is not a legal provision")

    # Test entity type validation
    assert validator.validate_entity_type("legal_provision")
    assert validator.validate_entity_type("legal_concept")
    assert not validator.validate_entity_type("invalid_type")

    # Test hierarchy path validation
    assert validator.validate_hierarchy_path(["phan", "chuong", "dieu"])
    assert validator.validate_hierarchy_path([])
    assert not validator.validate_hierarchy_path(["dieu", "chuong"])  # Wrong order
