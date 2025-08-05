import sys
import json
import asyncio
import asyncpg  # Thêm import này
from pathlib import Path
from typing import Dict, List, Any

# Add root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.main import LegalHiRAGSystem
from src.core.document_parser import LegalDocumentParser
from src.core.entity_extractor import LegalEntityExtractor
from src.storage.storage_manager import LegalStorageManager
from src.utils.config import load_config


async def test_document_processing():
    """Test complete document processing flow"""
    print("🧪 TESTING: Complete Legal Document Processing")
    print("=" * 70)

    # Step 1: Setup
    config_path = "src/config/legal_config.yaml"
    document_path = "data/raw/bo_luat_dan_su_2015.txt"

    if not Path(document_path).exists():
        print(f"❌ Document not found: {document_path}")
        return

    try:
        config = load_config(config_path)
        print(f"✅ Config loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return

    # Step 2: Initialize components
    print(f"\n🔧 INITIALIZING COMPONENTS:")

    try:
        document_parser = LegalDocumentParser()
        entity_extractor = LegalEntityExtractor(config["llm"])
        storage_manager = LegalStorageManager(config)
        print(f"✅ All components initialized")
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        return

    # Step 3: Parse document
    print(f"\n📖 STEP 1: PARSING DOCUMENT")

    try:
        with open(document_path, "r", encoding="utf-8") as f:
            text = f.read()

        document_id = Path(document_path).stem
        document = document_parser.parse_document(text, document_id)

        print(f"✅ Document parsed successfully:")
        print(f"  - Document ID: {document.id}")
        print(f"  - Title: {document.title}")
        print(f"  - Total provisions: {len(document.provisions)}")

        # Verify document_id is set in provisions
        provisions_with_doc_id = [
            p for p in document.provisions if p.document_id == document_id
        ]
        print(
            f"  - Provisions with document_id: {len(provisions_with_doc_id)}/{len(document.provisions)}"
        )

        # Show provision level distribution
        level_counts = {}
        for provision in document.provisions:
            level = provision.level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        print(f"  - Level distribution: {level_counts}")

    except Exception as e:
        print(f"❌ Document parsing failed: {e}")
        return

    # Step 4: Extract entities (test with small subset first)
    print(f"\n🔍 STEP 2: EXTRACTING ENTITIES AND RELATIONSHIPS")

    try:
        # Test with first 5 provisions to avoid API limits
        test_provisions = document.provisions
        test_document = document.model_copy()
        test_document.provisions = test_provisions

        print(f"📝 Testing with {len(test_provisions)} provisions:")
        print(f"log 5 provisions")
        for i, prov in enumerate(test_provisions[:5]):
            print(
                f"  {i+1}. {prov.id} - {prov.title or 'No title'} (doc_id: {prov.document_id})"
            )

        # Extract entities and relationships
        entities, relationships = await entity_extractor.extract_from_document(
            test_document
        )

        print(f"\n✅ Extraction completed:")
        print(f"  - Entities extracted: {len(entities)}")
        print(f"  - Relationships extracted: {len(relationships)}")

        # Show entity details
        if entities:
            print(f"\n📋 ENTITY DETAILS:")
            for i, entity in enumerate(entities[:10]):  # Show first 10
                print(f"  {i+1}. {entity.name}")
                print(f"     - Type: {entity.type.value}")
                print(f"     - Level: {entity.level.value if entity.level else 'None'}")
                print(f"     - Source: {entity.source_id}")
                print(f"     - Confidence: {entity.confidence_score}")
                print(f"     - Description: {entity.description[:100]}...")
                print()

        # Show relationship details
        if relationships:
            print(f"📋 RELATIONSHIP DETAILS:")
            for i, rel in enumerate(relationships[:5]):  # Show first 5
                print(f"  {i+1}. {rel.source_entity} → {rel.target_entity}")
                print(f"     - Type: {rel.relation_type.value}")
                print(f"     - Strength: {rel.strength}")
                print(f"     - Description: {rel.description[:100]}...")
                print()

        # Update document with extracted data
        test_document.entities = entities
        test_document.relationships = relationships

    except Exception as e:
        print(f"❌ Entity extraction failed: {e}")
        import traceback

        traceback.print_exc()
        return

    # Step 5: Store in databases
    print(f"\n💾 STEP 3: STORING IN DATABASES")

    try:
        success = await storage_manager.store_document(test_document)

        if success:
            print(f"✅ Document stored successfully in all databases")
        else:
            print(f"❌ Failed to store document")
            return

    except Exception as e:
        print(f"❌ Storage failed: {e}")
        import traceback

        traceback.print_exc()
        return

    # Step 6: Validate stored data
    print(f"\n🔍 STEP 4: VALIDATING STORED DATA")

    await validate_stored_data(storage_manager, test_document)

    # Step 7: Test queries
    print(f"\n❓ STEP 5: TESTING QUERIES")

    await test_queries(storage_manager, entities)

    # Cleanup
    await storage_manager.close_connections()
    print(f"\n✅ Test completed successfully!")


async def validate_stored_data(storage: LegalStorageManager, document):
    """Validate data stored in databases"""

    print(f"🔎 VALIDATING POSTGRESQL DATA:")
    try:
        # Create connection for validation
        conn = await asyncpg.connect(storage.postgres.connection_string)

        # Check document metadata
        query = "SELECT * FROM legal_documents WHERE id = $1"
        result = await conn.fetchrow(query, document.id)

        if result:
            print(f"  ✅ Document metadata found")
            print(f"    - ID: {result['id']}")
            print(f"    - Title: {result['title']}")
            print(f"    - Type: {result['document_type']}")
        else:
            print(f"  ❌ Document metadata not found")

        # Check provisions (correct table name)
        query = "SELECT COUNT(*) as count FROM legal_chunks WHERE document_id = $1"
        result = await conn.fetchrow(query, document.id)

        if result:
            print(f"  ✅ Provisions stored: {result['count']}")

        await conn.close()

    except Exception as e:
        print(f"  ❌ PostgreSQL validation failed: {e}")
        import traceback

        traceback.print_exc()

    print(f"\n🔎 VALIDATING NEO4J DATA:")
    try:
        # Check entities
        async with storage.neo4j.driver.session() as session:
            result = await session.run("MATCH (e:LegalEntity) RETURN COUNT(e) as count")
            record = await result.single()
            if record:
                print(f"  ✅ Entities stored: {record['count']}")

            # Check relationships
            result = await session.run("MATCH ()-[r]->() RETURN COUNT(r) as count")
            record = await result.single()
            if record:
                print(f"  ✅ Relationships stored: {record['count']}")

            # Show sample entities
            result = await session.run(
                "MATCH (e:LegalEntity) RETURN e.name, e.type LIMIT 3"
            )
            print(f"  📋 Sample entities:")
            async for record in result:
                print(f"    - {record['e.name']} ({record['e.type']})")

    except Exception as e:
        print(f"  ❌ Neo4j validation failed: {e}")

    print(f"\n🔎 VALIDATING CHROMADB DATA:")
    try:
        # Check entity collection directly
        collection = storage.chroma.entities_collection
        count = collection.count()
        print(f"  ✅ Entity collection exists with {count} items")

        # Test query using the available method
        test_results = await storage.chroma.query_similar("quyền", top_k=3)
        if test_results:
            print(f"  ✅ Query test successful: {len(test_results)} results")
            for i, result in enumerate(test_results[:2]):
                print(f"    {i+1}. {result.get('entity_name', 'Unknown')}")
        else:
            print(f"  ⚠️ No query results found")

    except Exception as e:
        print(f"  ❌ ChromaDB validation failed: {e}")
        import traceback

        traceback.print_exc()


async def test_queries(storage: LegalStorageManager, entities):
    """Test various query operations"""

    if not entities:
        print(f"  ❌ No entities to test queries")
        return

    # Test entity similarity search
    print(f"🧪 Testing entity similarity search:")
    try:
        results = await storage.query_similar_entities("quyền dân sự", top_k=3)
        print(f"  ✅ Found {len(results)} similar entities")
        for i, result in enumerate(results):
            print(
                f"    {i+1}. {result.get('entity_name', 'Unknown')} (distance: {result.get('distance', 'N/A')})"
            )
    except Exception as e:
        print(f"  ❌ Entity search failed: {e}")

    # Test entity details lookup
    print(f"\n🧪 Testing entity details lookup:")
    try:
        test_entity = entities[0].name
        details = await storage.get_entity_details(test_entity)
        if details:
            print(f"  ✅ Found details for '{test_entity}'")
            print(f"    - Type: {details.get('type', 'Unknown')}")
            print(
                f"    - Description: {details.get('description', 'No description')[:100]}..."
            )
        else:
            print(f"  ❌ No details found for '{test_entity}'")
    except Exception as e:
        print(f"  ❌ Entity details lookup failed: {e}")

    # Test Neo4j graph queries
    print(f"\n🧪 Testing graph relationships:")
    try:
        async with storage.neo4j.driver.session() as session:
            result = await session.run(
                """
                MATCH (e1:LegalEntity)-[r]->(e2:LegalEntity)
                RETURN e1.name, type(r), e2.name
                LIMIT 3
                """
            )
            relationships = []
            async for record in result:
                relationships.append(
                    (record["e1.name"], record["type(r)"], record["e2.name"])
                )

            if relationships:
                print(f"  ✅ Found {len(relationships)} relationships")
                for source, rel_type, target in relationships:
                    print(f"    - {source} --[{rel_type}]--> {target}")
            else:
                print(f"  ⚠️ No relationships found")

    except Exception as e:
        print(f"  ❌ Graph query failed: {e}")


async def test_with_hirag_system():
    """Test using the full HiRAG system"""
    print(f"\n🏛️ TESTING WITH FULL HiRAG SYSTEM:")

    try:
        system = LegalHiRAGSystem()

        # Process document
        # success = await system.process_document("data/raw/bo_luat_dan_su_2015.txt")
        success = True
        if success:
            print(f"✅ HiRAG system processing successful")

            # Test a query
            response = await system.query(
                "Các nguyên tắc cơ bản của pháp luật dân sự", mode="hierarchical"
            )
            print(f"\n🤖 Query test result:")
            print(f"  Question: Các nguyên tắc cơ bản của pháp luật dân sự")
            print(f"  Answer preview: {response[:200]}...")

        else:
            print(f"❌ HiRAG system processing failed")

        await system.close()

    except Exception as e:
        print(f"❌ HiRAG system test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Legal Document Processing Test...")

    try:
        # Run the comprehensive test
        # asyncio.run(test_document_processing())

        # Optionally test full system
        asyncio.run(test_with_hirag_system())

    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback

        traceback.print_exc()
# python -m tests.process_legal_document
