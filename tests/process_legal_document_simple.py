# tests/process_legal_document_simple.py
"""
Simplified Test for Legal Document Processing (No DB Dependencies)
- Parse document structure
- Extract entities and relationships (mock LLM)
- Show results without storing
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Add root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.document_parser import LegalDocumentParser
from src.models.legal_schemas import (
    LegalDocument,
    LegalEntity,
    LegalRelationship,
    LegalEntityType,
    LegalRelationType,
)


class MockLegalEntityExtractor:
    """Mock entity extractor for testing without LLM dependencies"""

    def __init__(self, llm_config=None):
        self.llm_config = llm_config

    async def extract_from_document(self, document: LegalDocument):
        """Mock entity extraction - creates entities based on document structure"""
        entities = []
        relationships = []

        print(
            f"🤖 Mock extracting entities from {len(document.provisions)} provisions..."
        )

        # Create mock entities from provisions
        for i, provision in enumerate(document.provisions[:10]):  # Limit to first 10
            # Create main entity from provision
            entity_name = f"Khái niệm_{provision.level.value}_{provision.number}"

            entity = LegalEntity(
                name=entity_name,
                type=LegalEntityType.LEGAL_CONCEPT,
                description=f"Khái niệm pháp lý từ {provision.level.value} {provision.number}",
                level=provision.level,
                source_id=provision.id,
                confidence_score=0.8 + (i % 3) * 0.1,
                synonyms=[],
                related_provisions=[provision.id],
            )
            entities.append(entity)

            # Create additional entities for Điều level
            if provision.level.value == "dieu" and len(entities) < 15:
                # Create legal procedure entity
                procedure_entity = LegalEntity(
                    name=f"Thủ_tục_{provision.number}",
                    type=LegalEntityType.LEGAL_PROCEDURE,
                    description=f"Thủ tục pháp lý từ Điều {provision.number}",
                    level=provision.level,
                    source_id=provision.id,
                    confidence_score=0.7 + (i % 4) * 0.05,
                    synonyms=[],
                    related_provisions=[provision.id],
                )
                entities.append(procedure_entity)

                # Create relationship between concept and procedure
                relationship = LegalRelationship(
                    source_entity=entity_name,
                    target_entity=f"Thủ_tục_{provision.number}",
                    relation_type=LegalRelationType.DEFINES,
                    description=f"Điều {provision.number} định nghĩa thủ tục",
                    strength=0.8,
                    source_id=provision.id,
                    bidirectional=False,
                )
                relationships.append(relationship)

        # Create some inter-entity relationships
        if len(entities) >= 2:
            for i in range(min(3, len(entities) - 1)):
                rel = LegalRelationship(
                    source_entity=entities[i].name,
                    target_entity=entities[i + 1].name,
                    relation_type=LegalRelationType.RELATES_TO,
                    description=f"Mối quan hệ giữa {entities[i].name} và {entities[i+1].name}",
                    strength=0.6 + (i * 0.1),
                    source_id=entities[i].source_id,
                    bidirectional=True,
                )
                relationships.append(rel)

        print(
            f"✅ Mock extraction completed: {len(entities)} entities, {len(relationships)} relationships"
        )
        return entities, relationships


def test_document_parsing():
    """Test document parsing only"""
    print("🧪 TESTING: Document Parsing")
    print("=" * 50)

    # Setup
    document_path = "data/raw/bo_luat_dan_su_2015.txt"

    if not Path(document_path).exists():
        print(f"❌ Document not found: {document_path}")
        return None

    # Parse document
    parser = LegalDocumentParser()

    try:
        with open(document_path, "r", encoding="utf-8") as f:
            text = f.read()

        document_id = Path(document_path).stem
        document = parser.parse_document(text, document_id)

        print(f"✅ Document parsed successfully:")
        print(f"  - Document ID: {document.id}")
        print(f"  - Title: {document.title}")
        print(f"  - Type: {document.document_type}")
        print(f"  - Total provisions: {len(document.provisions)}")

        # Show level distribution
        level_counts = {}
        for provision in document.provisions:
            level = provision.level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        print(f"  - Level distribution:")
        for level, count in level_counts.items():
            print(f"    • {level}: {count}")

        # Show sample provisions
        print(f"\n📋 SAMPLE PROVISIONS:")
        for i, prov in enumerate(document.provisions[:5]):
            print(f"  {i+1}. {prov.id}")
            print(f"     - Level: {prov.level.value}")
            print(f"     - Number: {prov.number}")
            print(f"     - Title: {prov.title or 'No title'}")
            print(f"     - Hierarchy: {' → '.join(prov.hierarchy_path)}")
            print(f"     - Content preview: {prov.content[:100]}...")
            print(f"     - Cross-refs: {prov.cross_references}")
            print()

        return document

    except Exception as e:
        print(f"❌ Document parsing failed: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_entity_extraction(document: LegalDocument):
    """Test entity extraction with mock extractor"""
    print("🧪 TESTING: Entity Extraction (Mock)")
    print("=" * 50)

    # Use mock extractor
    extractor = MockLegalEntityExtractor()

    try:
        # Test with subset to avoid too much output
        test_document = document.model_copy()
        test_document.provisions = document.provisions[:15]  # First 15 provisions

        print(f"📝 Testing with {len(test_document.provisions)} provisions")

        # Extract entities and relationships
        entities, relationships = await extractor.extract_from_document(test_document)

        print(f"\n📊 EXTRACTION RESULTS:")
        print(f"  - Entities: {len(entities)}")
        print(f"  - Relationships: {len(relationships)}")

        # Show entity details
        print(f"\n📋 ENTITIES EXTRACTED:")
        entity_types = {}
        entity_levels = {}

        for i, entity in enumerate(entities):
            print(f"  {i+1}. {entity.name}")
            print(f"     - Type: {entity.type.value}")
            print(f"     - Level: {entity.level.value if entity.level else 'None'}")
            print(f"     - Source: {entity.source_id}")
            print(f"     - Confidence: {entity.confidence_score:.2f}")
            print(f"     - Description: {entity.description}")
            print()

            # Collect stats
            entity_types[entity.type.value] = entity_types.get(entity.type.value, 0) + 1
            level = entity.level.value if entity.level else "None"
            entity_levels[level] = entity_levels.get(level, 0) + 1

        print(f"📈 ENTITY STATISTICS:")
        print(f"  - By Type: {entity_types}")
        print(f"  - By Level: {entity_levels}")

        # Show relationships
        print(f"\n🔗 RELATIONSHIPS EXTRACTED:")
        rel_types = {}

        for i, rel in enumerate(relationships):
            print(f"  {i+1}. {rel.source_entity} → {rel.target_entity}")
            print(f"     - Type: {rel.relation_type.value}")
            print(f"     - Strength: {rel.strength:.2f}")
            print(f"     - Description: {rel.description}")
            print(f"     - Bidirectional: {rel.bidirectional}")
            print()

            rel_types[rel.relation_type.value] = (
                rel_types.get(rel.relation_type.value, 0) + 1
            )

        print(f"📈 RELATIONSHIP STATISTICS:")
        print(f"  - By Type: {rel_types}")

        return entities, relationships

    except Exception as e:
        print(f"❌ Entity extraction failed: {e}")
        import traceback

        traceback.print_exc()
        return [], []


def test_data_structure_analysis(
    document: LegalDocument,
    entities: List[LegalEntity],
    relationships: List[LegalRelationship],
):
    """Analyze the data structures that would be stored"""
    print("🧪 TESTING: Data Structure Analysis")
    print("=" * 50)

    print(f"📊 DOCUMENT DATA STRUCTURE:")
    print(f"  - ID: {document.id}")
    print(f"  - Title: {document.title}")
    print(f"  - Document Type: {document.document_type}")
    print(f"  - Provisions Count: {len(document.provisions)}")
    print(f"  - Entities Count: {len(document.entities)}")
    print(f"  - Relationships Count: {len(document.relationships)}")
    print(
        f"  - Structure Keys: {list(document.structure.keys()) if document.structure else 'Empty'}"
    )

    print(f"\n💾 STORAGE DATA PREVIEW:")

    # PostgreSQL data preview
    print(f"📋 POSTGRESQL DATA:")
    print(f"  legal_documents table:")
    print(
        f"    INSERT INTO legal_documents (id, title, document_type, source_file, statistics, created_at)"
    )
    print(
        f"    VALUES ('{document.id}', '{document.title}', '{document.document_type}', ..."
    )

    print(f"  legal_provisions table ({len(document.provisions)} rows):")
    for prov in document.provisions[:3]:
        print(
            f"    INSERT: {prov.id}, {prov.level.value}, {prov.number}, '{prov.title}'..."
        )

    # Neo4j data preview
    print(f"\n🕸️ NEO4J DATA:")
    print(f"  LegalEntity nodes ({len(entities)} nodes):")
    for entity in entities[:3]:
        print(
            f"    CREATE (:LegalEntity {{name: '{entity.name}', type: '{entity.type.value}', ...}})"
        )

    print(f"  Relationships ({len(relationships)} relationships):")
    for rel in relationships[:3]:
        print(
            f"    CREATE (source)-[:RELATES {{type: '{rel.relation_type.value}'}}]->(target)"
        )

    # ChromaDB data preview
    print(f"\n🔍 CHROMADB DATA:")
    print(f"  legal_entities collection ({len(entities)} vectors):")
    for entity in entities[:3]:
        print(f"    Upsert: '{entity.name}' -> [embedding_vector] + metadata")

    print(f"\n📈 EXPECTED QUERY RESULTS:")
    print(f"  - Entity similarity search: Return top-k similar entities with scores")
    print(f"  - Graph traversal: Find paths between entities via relationships")
    print(f"  - Provision lookup: Get provisions by hierarchy path or cross-reference")
    print(f"  - Document structure: Navigate through legal hierarchy levels")


def save_test_results(
    document: LegalDocument,
    entities: List[LegalEntity],
    relationships: List[LegalRelationship],
):
    """Save test results to JSON for inspection"""
    output_dir = Path("tests/output")
    output_dir.mkdir(exist_ok=True)

    # Save document structure
    doc_data = {
        "id": document.id,
        "title": document.title,
        "document_type": document.document_type,
        "provisions_count": len(document.provisions),
        "sample_provisions": [
            {
                "id": prov.id,
                "level": prov.level.value,
                "number": prov.number,
                "title": prov.title,
                "hierarchy_path": prov.hierarchy_path,
                "content_preview": prov.content[:200],
            }
            for prov in document.provisions[:10]
        ],
    }

    with open(output_dir / "document_structure.json", "w", encoding="utf-8") as f:
        json.dump(doc_data, f, ensure_ascii=False, indent=2)

    # Save entities
    entities_data = [
        {
            "name": entity.name,
            "type": entity.type.value,
            "level": entity.level.value if entity.level else None,
            "source_id": entity.source_id,
            "confidence_score": entity.confidence_score,
            "description": entity.description,
        }
        for entity in entities
    ]

    with open(output_dir / "extracted_entities.json", "w", encoding="utf-8") as f:
        json.dump(entities_data, f, ensure_ascii=False, indent=2)

    # Save relationships
    relationships_data = [
        {
            "source_entity": rel.source_entity,
            "target_entity": rel.target_entity,
            "relation_type": rel.relation_type.value,
            "description": rel.description,
            "strength": rel.strength,
            "source_id": rel.source_id,
        }
        for rel in relationships
    ]

    with open(output_dir / "extracted_relationships.json", "w", encoding="utf-8") as f:
        json.dump(relationships_data, f, ensure_ascii=False, indent=2)

    print(f"💾 Test results saved to tests/output/")


async def main():
    """Main test function"""
    print("🚀 Starting Simplified Legal Document Processing Test...")
    print()

    try:
        # Step 1: Test document parsing
        document = test_document_parsing()
        if not document:
            return

        print("\n" + "=" * 70 + "\n")

        # Step 2: Test entity extraction
        entities, relationships = await test_entity_extraction(document)
        if not entities:
            return

        # Update document with extracted data
        document.entities = entities
        document.relationships = relationships

        print("\n" + "=" * 70 + "\n")

        # Step 3: Analyze data structures
        test_data_structure_analysis(document, entities, relationships)

        print("\n" + "=" * 70 + "\n")

        # Step 4: Save results
        save_test_results(document, entities, relationships)

        print(f"\n✅ All tests completed successfully!")
        print(f"📄 Check tests/output/ for detailed results")

    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
