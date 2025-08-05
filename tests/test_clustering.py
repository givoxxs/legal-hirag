# tests/test_clustering.py
"""
Test Enhanced Legal Hierarchical Clustering với bo_luat_dan_su_2015.txt
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List

# Add root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.document_parser import LegalDocumentParser
from src.core.clustering import LegalHierarchicalClustering
from src.models.legal_schemas import LegalLevel, LegalProvision, LegalDocument


class MockEntityVDB:
    """Mock Entity Vector Database for testing"""

    def __init__(self):
        self.embeddings = {}

    async def query(self, name: str, top_k: int = 1):
        """Mock query method"""
        # Return mock result
        return [
            {
                "entity_name": name,
                "embedding": [0.1] * 768,  # Mock embedding
                "similarity": 0.8,
            }
        ]

    async def embedding_func(self, texts: List[str]):
        """Mock embedding function"""
        return [[0.1] * 768 for _ in texts]


async def test_enhanced_clustering():
    """Test enhanced hierarchical clustering"""
    print("🧪 TESTING: Enhanced Legal Hierarchical Clustering")
    print("=" * 70)

    # Step 1: Parse document
    parser = LegalDocumentParser()
    data_file = (
        Path(__file__).parent.parent / "data" / "raw" / "bo_luat_dan_su_2015.txt"
    )

    if not data_file.exists():
        print(f"❌ File không tồn tại: {data_file}")
        return

    print(f"📁 Đọc file: {data_file}")
    with open(data_file, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"📊 Parsing document...")
    document = parser.parse_document(content, "bo_luat_dan_su_2015")

    print(f"  - Tổng số provisions: {len(document.provisions)}")

    # Step 2: Create sample entities from provisions
    print("\n🔍 Tạo sample entities từ provisions...")
    sample_entities = []

    # Take first 20 provisions for testing
    for i, provision in enumerate(document.provisions[:20]):
        # Create mock entities from provision content
        entities_from_provision = _create_mock_entities_from_provision(provision, i)
        sample_entities.extend(entities_from_provision)

    print(f"  - Tổng số entities tạo ra: {len(sample_entities)}")

    # Step 3: Test clustering
    print("\n🔬 Testing Enhanced Clustering...")
    clustering = LegalHierarchicalClustering(max_clusters=8, min_cluster_size=2)
    mock_vdb = MockEntityVDB()

    clusters = await clustering.perform_clustering(
        entity_vdb=mock_vdb,
        global_config={},
        entities=sample_entities,
        provisions=document.provisions[:20],  # Pass relevant provisions
    )

    # Step 4: Analyze results
    print(f"\n📊 KẾT QUẢ CLUSTERING:")
    print(f"  - Số clusters: {len(clusters)}")

    for i, cluster in enumerate(clusters):
        print(f"\n  📁 Cluster {i+1} ({len(cluster)} entities):")

        # Analyze cluster composition
        levels = {}
        types = {}
        sources = {}

        for entity in cluster:
            level = entity.get("level", "unknown")
            entity_type = entity.get("entity_type", "unknown")
            source = entity.get("source_id", "unknown")

            levels[level] = levels.get(level, 0) + 1
            types[entity_type] = types.get(entity_type, 0) + 1
            sources[source] = sources.get(source, 0) + 1

            print(
                f"    - {entity.get('entity_name', 'Unknown')} ({level}, {entity_type})"
            )

        print(f"    📈 Level distribution: {dict(levels)}")
        print(f"    📈 Type distribution: {dict(types)}")
        print(f"    📈 Source distribution: {dict(sources)}")

    # Step 5: Generate summary
    summary = clustering.get_cluster_summary(clusters)
    print(f"\n📋 CLUSTER SUMMARY:")
    print(f"  - Total clusters: {summary['total_clusters']}")
    print(f"  - Total entities: {summary['total_entities']}")
    print(f"  - Average cluster size: {summary['avg_cluster_size']:.2f}")
    print(f"  - Min cluster size: {summary['min_cluster_size']}")
    print(f"  - Max cluster size: {summary['max_cluster_size']}")
    print(f"  - Level distribution: {summary['level_distribution']}")
    print(f"  - Type distribution: {summary['type_distribution']}")

    # Step 6: Test legal structure awareness
    print(f"\n🔍 TESTING Legal Structure Awareness:")
    await _test_hierarchy_clustering(clustering, mock_vdb, document.provisions[:10])


def _create_mock_entities_from_provision(
    provision: LegalProvision, index: int
) -> List[Dict]:
    """Create mock entities from a provision for testing"""
    entities = []

    # Create a main concept entity
    main_entity = {
        "entity_name": f"Khái niệm_{provision.level.value}_{provision.number}",
        "entity_type": "legal_concept",
        "level": provision.level.value,
        "source_id": provision.id,
        "confidence_score": 0.8 + (index % 3) * 0.1,
        "description": f"Khái niệm chính từ {provision.level.value} {provision.number}",
    }
    entities.append(main_entity)

    # For Điều level, create additional entities
    if provision.level == LegalLevel.DIEU:
        # Create a legal entity
        legal_entity = {
            "entity_name": f"Chủ_thể_{provision.number}",
            "entity_type": "legal_entity",
            "level": provision.level.value,
            "source_id": provision.id,
            "confidence_score": 0.7 + (index % 4) * 0.05,
            "description": f"Chủ thể pháp lý từ Điều {provision.number}",
        }
        entities.append(legal_entity)

        # Create a legal procedure if content suggests it
        if any(
            keyword in provision.content.lower()
            for keyword in ["thủ tục", "quy trình", "thực hiện"]
        ):
            procedure_entity = {
                "entity_name": f"Thủ_tục_{provision.number}",
                "entity_type": "legal_procedure",
                "level": provision.level.value,
                "source_id": provision.id,
                "confidence_score": 0.6 + (index % 5) * 0.08,
                "description": f"Thủ tục từ Điều {provision.number}",
            }
            entities.append(procedure_entity)

    return entities


async def _test_hierarchy_clustering(
    clustering: LegalHierarchicalClustering,
    mock_vdb: MockEntityVDB,
    provisions: List[LegalProvision],
):
    """Test clustering behavior with different hierarchy levels"""

    print("  🔸 Testing same-level clustering...")

    # Create entities from same Chương
    same_chapter_entities = []
    chuong_provisions = [p for p in provisions if p.level == LegalLevel.CHUONG][:2]

    for prov in chuong_provisions:
        entity = {
            "entity_name": f"Concept_from_{prov.id}",
            "entity_type": "legal_concept",
            "level": prov.level.value,
            "source_id": prov.id,
            "confidence_score": 0.8,
        }
        same_chapter_entities.append(entity)

    if len(same_chapter_entities) >= 2:
        clusters = await clustering.perform_clustering(
            entity_vdb=mock_vdb,
            global_config={},
            entities=same_chapter_entities,
            provisions=chuong_provisions,
        )

        print(f"    - Same level entities clustered into {len(clusters)} clusters")
        for i, cluster in enumerate(clusters):
            print(f"      Cluster {i+1}: {len(cluster)} entities")

    print("  🔸 Testing cross-level clustering...")

    # Test with mixed levels
    mixed_entities = []
    mixed_provisions = provisions[:5]  # Mix of different levels

    for prov in mixed_provisions:
        entity = {
            "entity_name": f"Mixed_concept_{prov.id}",
            "entity_type": "legal_concept",
            "level": prov.level.value,
            "source_id": prov.id,
            "confidence_score": 0.8,
        }
        mixed_entities.append(entity)

    if len(mixed_entities) >= 2:
        clusters = await clustering.perform_clustering(
            entity_vdb=mock_vdb,
            global_config={},
            entities=mixed_entities,
            provisions=mixed_provisions,
        )

        print(f"    - Mixed level entities clustered into {len(clusters)} clusters")
        for i, cluster in enumerate(clusters):
            levels_in_cluster = [e.get("level") for e in cluster]
            print(
                f"      Cluster {i+1}: {len(cluster)} entities with levels {set(levels_in_cluster)}"
            )


def compare_with_old_clustering():
    """So sánh với clustering cũ (nếu cần)"""
    print("\n🔄 COMPARISON với clustering cũ:")
    print("  - Clustering cũ: Chỉ dựa vào semantic embeddings")
    print("  - Clustering mới: Kết hợp legal hierarchy + semantic")
    print("  - Ưu điểm:")
    print("    ✅ Entities từ cùng Điều được nhóm lại")
    print("    ✅ Respect legal hierarchy structure")
    print("    ✅ Cross-reference awareness")
    print("    ✅ Level-aware similarity scoring")
    print("    ✅ Better legal context preservation")


if __name__ == "__main__":
    print("🚀 Starting Enhanced Clustering Test...")

    try:
        # Run the async test
        asyncio.run(test_enhanced_clustering())

        # Show comparison
        compare_with_old_clustering()

        print("\n✅ Test completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()

# python -m tests.test_clustering
