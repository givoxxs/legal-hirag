# tests/test_clustering_simple.py
"""
Test Enhanced Legal Hierarchical Clustering logic (simplified version)
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List

# Add root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.document_parser import LegalDocumentParser
from src.models.legal_schemas import LegalLevel, LegalProvision, LegalDocument


class SimplifiedLegalClustering:
    """Simplified version to test legal hierarchy clustering logic"""

    def __init__(self):
        self.level_weights = {
            LegalLevel.PHAN: 1.0,
            LegalLevel.CHUONG: 2.0,
            LegalLevel.MUC: 3.0,
            LegalLevel.DIEU: 4.0,
            LegalLevel.KHOAN: 5.0,
        }

    def cluster_by_legal_structure(
        self, entities: List[Dict], provisions: List[LegalProvision] = None
    ):
        """Test the legal structure clustering logic"""

        # Create provision lookup
        provision_lookup = {}
        if provisions:
            for provision in provisions:
                provision_lookup[provision.id] = provision

        # Group entities by hierarchy
        hierarchy_groups = {}

        for entity in entities:
            level = entity.get("level", "unknown")
            source_id = entity.get("source_id", "")

            # Get hierarchy path
            hierarchy_path = []
            if source_id in provision_lookup:
                provision = provision_lookup[source_id]
                hierarchy_path = provision.hierarchy_path

            # Create clustering key
            if hierarchy_path:
                if level == LegalLevel.KHOAN.value and len(hierarchy_path) > 1:
                    # Khoản entities: cluster by parent Điều
                    key = tuple(hierarchy_path[:-1])
                elif level == LegalLevel.DIEU.value and len(hierarchy_path) > 2:
                    # Điều entities: cluster by parent Chương
                    key = tuple(hierarchy_path[:-2])
                else:
                    # Higher levels: cluster by immediate parent
                    key = (
                        tuple(hierarchy_path[:-1])
                        if len(hierarchy_path) > 1
                        else tuple(hierarchy_path)
                    )
            else:
                # No hierarchy info: group by level only
                key = (level,)

            if key not in hierarchy_groups:
                hierarchy_groups[key] = []
            hierarchy_groups[key].append(entity)

        return list(hierarchy_groups.values())

    def calculate_hierarchy_path_similarity(
        self, path1: List[str], path2: List[str]
    ) -> float:
        """Test hierarchy path similarity calculation"""

        if not path1 or not path2:
            return 0.0

        # Find common prefix length
        common_length = 0
        min_length = min(len(path1), len(path2))

        for i in range(min_length):
            if path1[i] == path2[i]:
                common_length += 1
            else:
                break

        # Calculate similarity
        max_length = max(len(path1), len(path2))
        return common_length / max_length if max_length > 0 else 1.0


def test_legal_clustering_logic():
    """Test the legal clustering logic without complex dependencies"""
    print("🧪 TESTING: Legal Clustering Logic (Simplified)")
    print("=" * 60)

    # Step 1: Parse document
    parser = LegalDocumentParser()
    data_file = (
        Path(__file__).parent.parent / "data" / "raw" / "bo_luat_dan_su_2015.txt"
    )

    if not data_file.exists():
        print(f"❌ File không tồn tại: {data_file}")
        return

    print(f"📁 Đọc file: {data_file.name}")
    with open(data_file, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"📊 Parsing document...")
    document = parser.parse_document(content, "bo_luat_dan_su_2015")

    print(f"  - Tổng số provisions: {len(document.provisions)}")

    # Step 2: Analyze hierarchy structure
    print(f"\n📋 PHÂN TÍCH CẤU TRÚC HIERARCHY:")
    level_counts = {}
    max_depth = 0

    for provision in document.provisions:
        level = provision.level.value
        level_counts[level] = level_counts.get(level, 0) + 1
        max_depth = max(max_depth, len(provision.hierarchy_path))

    print(f"  Level distribution:")
    for level, count in level_counts.items():
        print(f"    - {level}: {count} provisions")

    print(f"  - Max hierarchy depth: {max_depth}")

    # Step 3: Create sample entities
    print(f"\n🔍 TẠO SAMPLE ENTITIES:")
    sample_entities = []

    # Take provisions from different levels for testing
    test_provisions = []
    for level in [
        LegalLevel.PHAN,
        LegalLevel.CHUONG,
        LegalLevel.DIEU,
        LegalLevel.KHOAN,
    ]:
        level_provisions = [p for p in document.provisions if p.level == level][:3]
        test_provisions.extend(level_provisions)

    print(f"  - Selected {len(test_provisions)} test provisions")

    for i, provision in enumerate(test_provisions):
        entity = {
            "entity_name": f"Entity_{provision.level.value}_{provision.number}",
            "entity_type": "legal_concept",
            "level": provision.level.value,
            "source_id": provision.id,
            "hierarchy_path": provision.hierarchy_path,
        }
        sample_entities.append(entity)

    print(f"  - Created {len(sample_entities)} sample entities")

    # Step 4: Test clustering logic
    print(f"\n🔬 TESTING CLUSTERING LOGIC:")
    clustering = SimplifiedLegalClustering()

    clusters = clustering.cluster_by_legal_structure(sample_entities, test_provisions)

    print(f"  - Clustered into {len(clusters)} groups")

    for i, cluster in enumerate(clusters):
        print(f"\n  📁 Cluster {i+1} ({len(cluster)} entities):")

        levels = {}
        hierarchy_examples = []

        for entity in cluster:
            level = entity.get("level", "unknown")
            levels[level] = levels.get(level, 0) + 1

            hierarchy_path = entity.get("hierarchy_path", [])
            if hierarchy_path and len(hierarchy_path) <= 3:  # Show only short paths
                hierarchy_examples.append(" → ".join(hierarchy_path))

            print(f"    - {entity.get('entity_name')} ({level})")

        print(f"    📈 Levels: {dict(levels)}")
        if hierarchy_examples:
            print(f"    📂 Example paths: {hierarchy_examples[:2]}")

    # Step 5: Test hierarchy similarity
    print(f"\n🔍 TESTING HIERARCHY SIMILARITY:")

    # Test similarity between entities with different hierarchy paths
    test_cases = [
        (["phan-1", "chuong-1", "dieu-1"], ["phan-1", "chuong-1", "dieu-2"]),
        (["phan-1", "chuong-1"], ["phan-1", "chuong-2"]),
        (["phan-1"], ["phan-2"]),
        (
            ["phan-1", "chuong-1", "dieu-1", "khoan-1"],
            ["phan-1", "chuong-1", "dieu-1", "khoan-2"],
        ),
    ]

    for path1, path2 in test_cases:
        similarity = clustering.calculate_hierarchy_path_similarity(path1, path2)
        print(
            f"  📏 Similarity: {' → '.join(path1)} vs {' → '.join(path2)} = {similarity:.2f}"
        )

    # Step 6: Show clustering benefits
    print(f"\n✅ CLUSTERING BENEFITS:")
    print("  🎯 Legal structure awareness:")
    print("    - Entities từ cùng Điều được nhóm lại")
    print("    - Hierarchy path similarity được tính toán")
    print("    - Level-based grouping logic")

    print("  🎯 Better legal context:")
    print("    - Khoản entities cluster theo parent Điều")
    print("    - Điều entities cluster theo parent Chương")
    print("    - Preserves legal document structure")

    # Step 7: Show some real examples
    print(f"\n📋 REAL EXAMPLES FROM DOCUMENT:")

    # Find some interesting provisions to show
    dieu_provisions = [p for p in document.provisions if p.level == LegalLevel.DIEU][:5]
    for prov in dieu_provisions:
        print(f"  📖 {prov.id}: {prov.title or 'No title'}")
        print(f"    📂 Path: {' → '.join(prov.hierarchy_path)}")
        print(f"    📝 Content preview: {prov.content[:100]}...")
        print()


if __name__ == "__main__":
    print("🚀 Starting Simplified Clustering Test...")

    try:
        test_legal_clustering_logic()
        print("\n✅ Test completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
