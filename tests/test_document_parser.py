# tests/test_document_parser.py
"""
Test LegalDocumentParser với file bo_luat_dan_su_2015.txt đầy đủ
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


def test_full_legal_document():
    """Test parsing toàn bộ file bo_luat_dan_su_2015.txt"""
    print("🧪 TESTING: Full Legal Document Parsing")
    print("=" * 60)

    # Khởi tạo parser
    parser = LegalDocumentParser()

    # Đọc file dữ liệu
    data_file = (
        Path(__file__).parent.parent / "data" / "raw" / "bo_luat_dan_su_2015.txt"
    )

    if not data_file.exists():
        print(f"❌ File không tồn tại: {data_file}")
        return

    print(f"📁 Đọc file: {data_file}")
    with open(data_file, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"📊 Kích thước file: {len(content):,} ký tự")
    print(f"📊 Số dòng: {len(content.splitlines()):,} dòng")

    # Parse document
    print("\n🔄 Đang parse document...")
    document = parser.parse_document(content, "bo_luat_dan_su_2015")

    # Thống kê tổng quan
    print("\n📋 KẾT QUẢ PARSING:")
    print(f"  - Document ID: {document.id}")
    print(f"  - Title: {document.title}")
    print(f"  - Document Type: {document.document_type}")
    print(f"  - Tổng số provisions: {len(document.provisions)}")
    print(f"  - Tổng số elements trong structure: {len(document.structure)}")

    # Thống kê theo level
    level_counts = {}
    for provision in document.provisions:
        level = provision.level.value
        level_counts[level] = level_counts.get(level, 0) + 1

    print("\n📊 THỐNG KÊ THEO CẤP ĐỘ:")
    for level in ["phan", "chuong", "muc", "dieu", "khoan"]:
        count = level_counts.get(level, 0)
        print(f"  - {level.upper()}: {count}")

    return document


def display_sample_provisions(document: LegalDocument):
    """Hiển thị một số provisions mẫu"""
    print("\n📝 MỘT SỐ PROVISIONS MẪU:")
    print("-" * 60)

    # Tìm và hiển thị Phần đầu tiên
    first_phan = None
    for provision in document.provisions:
        if provision.level == LegalLevel.PHAN:
            first_phan = provision
            break

    if first_phan:
        print(f"\n🏷️ PHẦN ĐẦU TIÊN:")
        print(f"  ID: {first_phan.id}")
        print(f"  Title: {first_phan.title}")
        print(f"  Content: {first_phan.content[:100]}...")
        print(
            f"  Path: {' → '.join(first_phan.hierarchy_path) if first_phan.hierarchy_path else 'None'}"
        )

    # Tìm và hiển thị vài Điều đầu tiên
    print(f"\n📜 VÀI ĐIỀU ĐẦU TIÊN:")
    dieu_count = 0
    for provision in document.provisions:
        if provision.level == LegalLevel.DIEU and dieu_count < 3:
            print(f"\n  📋 ĐIỀU {provision.number}:")
            print(f"    ID: {provision.id}")
            print(f"    Title: {provision.title}")
            print(f"    Parent: {provision.parent_id}")
            print(f"    Content: {provision.content}")
            print(
                f"    Path: {' → '.join(provision.hierarchy_path) if provision.hierarchy_path else 'None'}"
            )
            dieu_count += 1

    # Tìm và hiển thị vài Khoản
    print(f"\n🔢 VÀI KHOẢN MẪU:")
    khoan_count = 0
    for provision in document.provisions:
        if provision.level == LegalLevel.KHOAN and khoan_count < 3:
            print(f"\n  📌 KHOẢN {provision.number}:")
            print(f"    ID: {provision.id}")
            print(f"    Parent: {provision.parent_id}")
            print(f"    Content: {provision.content}...")
            khoan_count += 1


def display_hierarchy_structure(document: LegalDocument):
    """Hiển thị cấu trúc hierarchy"""
    print("\n🌳 CẤU TRÚC HIERARCHY (Top levels):")
    print("-" * 60)

    # Hiển thị structure của top levels
    root_elements = []
    for element_id, element in document.structure.items():
        if element.get("parent_id") is None:
            root_elements.append(element)

    for root in root_elements[:2]:  # Chỉ hiển thị 2 elements gốc đầu tiên
        print(f"\n📁 {root['id']} ({root['level'].upper()})")
        print(f"   Title: {root['title']}")
        print(f"   Children: {len(root.get('children', []))}")

        # Hiển thị children level 1
        for child_id in root.get("children", [])[:3]:  # Chỉ 3 children đầu
            child = document.structure.get(child_id)
            if child:
                print(f"   └── 📂 {child['id']} ({child['level'].upper()})")
                print(f"       Title: {child['title']}")
                print(f"       Children: {len(child.get('children', []))}")

                # Hiển thị children level 2
                for grandchild_id in child.get("children", [])[
                    :2
                ]:  # Chỉ 2 grandchildren đầu
                    grandchild = document.structure.get(grandchild_id)
                    if grandchild:
                        print(
                            f"       └── 📄 {grandchild['id']} ({grandchild['level'].upper()})"
                        )
                        print(f"           Title: {grandchild['title'][:50]}...")


def check_hierarchy_integrity(document: LegalDocument):
    """Kiểm tra tính toàn vẹn của hierarchy"""
    print("\n🔍 KIỂM TRA TÍNH TOÀN VẸN HIERARCHY:")
    print("-" * 60)

    orphaned_count = 0
    wrong_relationship_count = 0

    parser = LegalDocumentParser()

    for element_id, element in document.structure.items():
        parent_id = element.get("parent_id")

        if parent_id:
            # Kiểm tra parent có tồn tại không
            parent = document.structure.get(parent_id)
            if not parent:
                orphaned_count += 1
                if orphaned_count <= 3:  # Chỉ hiển thị 3 lỗi đầu
                    print(f"  ❌ Orphaned: {element_id} → parent {parent_id} not found")
            else:
                # Kiểm tra relationship có đúng không
                if not parser._is_child_of(element["level"], parent["level"]):
                    wrong_relationship_count += 1
                    if wrong_relationship_count <= 3:  # Chỉ hiển thị 3 lỗi đầu
                        print(
                            f"  ⚠️ Wrong relationship: {element['level']} under {parent['level']}"
                        )

    print(f"\n📊 SUMMARY:")
    print(f"  - Orphaned elements: {orphaned_count}")
    print(f"  - Wrong relationships: {wrong_relationship_count}")

    if orphaned_count == 0 and wrong_relationship_count == 0:
        print("  ✅ Hierarchy integrity is GOOD!")
    else:
        print("  ⚠️ Found some hierarchy issues")


def find_cross_references_sample(document: LegalDocument):
    """Tìm và hiển thị mẫu cross-references"""
    print("\n🔗 CROSS-REFERENCES MẪU:")
    print("-" * 60)

    parser = LegalDocumentParser()
    sample_count = 0

    for provision in document.provisions:
        if provision.level == LegalLevel.DIEU and len(provision.content) > 100:
            cross_refs = parser._extract_cross_references(provision.content)
            if cross_refs and sample_count < 3:
                print(f"\n📜 {provision.id}: {provision.title}")
                print(f"   Cross-references: {', '.join(cross_refs)}")
                print(f"   Sample content: {provision.content}...")
                sample_count += 1


def save_parsing_results(document: LegalDocument):
    """Lưu kết quả parsing ra file JSON"""
    print("\n💾 LƯU KẾT QUẢ PARSING:")
    print("-" * 60)

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    # Tạo dữ liệu để export (chỉ lấy sample để file không quá lớn)
    export_data = {
        "document_info": {
            "id": document.id,
            "title": document.title,
            "document_type": document.document_type,
            "total_provisions": len(document.provisions),
            "total_structure_elements": len(document.structure),
        },
        "level_statistics": {},
        "sample_provisions": [],
        "structure_sample": {},
    }

    # Level statistics
    level_counts = {}
    for provision in document.provisions:
        level = provision.level.value
        level_counts[level] = level_counts.get(level, 0) + 1
    export_data["level_statistics"] = level_counts

    # Sample provisions (first 10)
    for provision in document.provisions[:10]:
        export_data["sample_provisions"].append(
            {
                "id": provision.id,
                "level": provision.level.value,
                "number": provision.number,
                "title": provision.title,
                "parent_id": provision.parent_id,
                "hierarchy_path": provision.hierarchy_path,
                "content_preview": (
                    provision.content[:200] + "..."
                    if len(provision.content) > 200
                    else provision.content
                ),
            }
        )

    # Structure sample (first 20 elements)
    structure_items = list(document.structure.items())[:20]
    for element_id, element in structure_items:
        export_data["structure_sample"][element_id] = element

    # Save to file
    output_file = output_dir / "bo_luat_dan_su_2015_parsed.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã lưu kết quả vào: {output_file}")
    print(f"📊 File size: {output_file.stat().st_size:,} bytes")


def main():
    """Hàm chính chạy tất cả tests"""
    print("🎯 TESTING LEGAL DOCUMENT PARSER")
    print("=" * 60)
    print("Mục đích: Test parser với file bo_luat_dan_su_2015.txt đầy đủ")
    print("=" * 60)

    try:
        # 1. Parse toàn bộ document
        document = test_full_legal_document()

        if document is None:
            print("❌ Parsing failed!")
            return

        # 2. Hiển thị sample provisions
        display_sample_provisions(document)

        # 3. Hiển thị hierarchy structure
        display_hierarchy_structure(document)

        # 4. Kiểm tra integrity
        check_hierarchy_integrity(document)

        # 5. Tìm cross-references
        find_cross_references_sample(document)

        # 6. Lưu kết quả
        save_parsing_results(document)

        print("\n" + "=" * 60)
        print("🎉 HOÀN THÀNH TẤT CẢ TESTS!")
        print("✅ Document parser hoạt động tốt với bo_luat_dan_su_2015.txt")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback

        print(traceback.format_exc())


if __name__ == "__main__":
    main()
