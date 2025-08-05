# demo_document_parser_explained.py
"""
DEMO GIẢI THÍCH CHI TIẾT document_parser.py

Mục đích: Hiểu rõ từng hàm và cách hoạt động của LegalDocumentParser
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.document_parser import LegalDocumentParser


def demo_1_pattern_matching():
    """
    DEMO 1: _match_legal_pattern()
    Chức năng: Nhận dạng các pattern của văn bản pháp luật
    """
    print("🔍 DEMO 1: PATTERN MATCHING")
    print("=" * 50)

    parser = LegalDocumentParser()

    # Hiển thị các patterns được sử dụng
    print("📋 Các patterns regex được sử dụng:")
    for level, pattern in parser.patterns.items():
        print(f"  - {level}: {pattern}")

    print("\n🧪 Test với các dòng mẫu:")

    test_lines = [
        "PHẦN THỨ NHẤT: QUY ĐỊNH CHUNG",
        "CHƯƠNG I: NHỮNG QUY ĐỊNH CHUNG",
        "MỤC 1: NĂNG LỰC PHÁP LUẬT DÂN SỰ",
        "Điều 1. Phạm vi điều chỉnh",
        "1. Ở nước Cộng hòa xã hội chủ nghĩa Việt Nam",
        "Bộ luật này quy định địa vị pháp lý",  # Không match
    ]

    for line in test_lines:
        result = parser._match_legal_pattern(line)
        if result:
            level, number, title = result
            print(f"✅ '{line}' → Level: {level}, Number: {number}, Title: {title}")
        else:
            print(f"❌ '{line}' → Không match pattern nào")

    print("\n💡 Giải thích:")
    print("- Level: cấp độ pháp luật (phan, chuong, muc, dieu, khoan)")
    print("- Number: số thứ tự (I, II, 1, 2, ...)")
    print("- Title: tiêu đề của điều khoản")


def demo_2_hierarchy_relationships():
    """
    DEMO 2: _is_child_of()
    Chức năng: Kiểm tra quan hệ cha-con trong hierarchy
    """
    print("\n\n👶 DEMO 2: HIERARCHY RELATIONSHIPS")
    print("=" * 50)

    parser = LegalDocumentParser()

    print("📊 Thứ tự hierarchy:")
    for i, level in enumerate(parser.hierarchy_order):
        print(f"  {i+1}. {level}")

    print("\n🧪 Test quan hệ cha-con:")

    test_relationships = [
        ("chuong", "phan", True),  # Chương thuộc Phần ✅
        ("muc", "chuong", True),  # Mục thuộc Chương ✅
        ("dieu", "muc", True),  # Điều thuộc Mục ✅
        ("khoan", "dieu", True),  # Khoản thuộc Điều ✅
        ("phan", "chuong", False),  # Phần KHÔNG thuộc Chương ❌
        ("dieu", "khoan", False),  # Điều KHÔNG thuộc Khoản ❌
    ]

    for child, parent, expected in test_relationships:
        result = parser._is_child_of(child, parent)
        status = "✅" if result == expected else "❌"
        print(f"{status} {child} là con của {parent}? {result} (expected: {expected})")

    print("\n💡 Giải thích:")
    print("- Quan hệ dựa trên index trong hierarchy_order")
    print("- Child có index > Parent index → True")
    print("- Ví dụ: dieu (index=3) > muc (index=2) → True")


def demo_3_extract_provisions():
    """
    DEMO 3: _extract_provisions()
    Chức năng: Tách văn bản thành các LegalProvision objects
    """
    print("\n\n📝 DEMO 3: EXTRACT PROVISIONS")
    print("=" * 50)

    parser = LegalDocumentParser()

    # Văn bản mẫu nhỏ
    sample_text = """BỘ LUẬT DÂN SỰ 2015
PHẦN THỨ NHẤT: QUY ĐỊNH CHUNG
CHƯƠNG I: NHỮNG QUY ĐỊNH CHUNG
Điều 1. Phạm vi điều chỉnh
Bộ luật này quy định địa vị pháp lý, chuẩn mực pháp lý về cách ứng xử của cá nhân, pháp nhân.
Điều 2. Công nhận, tôn trọng, bảo vệ và bảo đảm quyền dân sự
1. Ở nước Cộng hòa xã hội chủ nghĩa Việt Nam, các quyền dân sự được công nhận.
2. Quyền dân sự chỉ có thể bị hạn chế theo quy định của luật."""

    provisions = parser._extract_provisions(sample_text)

    print(f"📊 Tổng số provisions: {len(provisions)}")

    for i, provision in enumerate(provisions):
        print(f"\n📋 Provision {i+1}:")
        print(f"  - ID: {provision.id}")
        print(f"  - Level: {provision.level.value}")
        print(f"  - Number: {provision.number}")
        print(f"  - Title: {provision.title}")
        print(f"  - Content: {provision.content[:100]}...")

    print("\n💡 Giải thích:")
    print("- Mỗi dòng match pattern → tạo LegalProvision mới")
    print("- Content buffer thu thập nội dung cho đến khi gặp pattern tiếp theo")
    print("- ID format: {level}-{number}")


def demo_4_build_hierarchy():
    """
    DEMO 4: _build_hierarchy()
    Chức năng: Xây dựng cây phân cấp từ danh sách provisions
    """
    print("\n\n🌳 DEMO 4: BUILD HIERARCHY")
    print("=" * 50)

    parser = LegalDocumentParser()

    # Tạo sample provisions
    sample_text = """PHẦN THỨ NHẤT: QUY ĐỊNH CHUNG
CHƯƠNG I: NHỮNG QUY ĐỊNH CHUNG
Điều 1. Phạm vi điều chỉnh
Bộ luật này quy định địa vị pháp lý.
Điều 2. Công nhận quyền dân sự
1. Ở nước Việt Nam các quyền được công nhận.
2. Quyền có thể bị hạn chế."""

    provisions = parser._extract_provisions(sample_text)
    hierarchy = parser._build_hierarchy(provisions)

    print("🌳 Cấu trúc hierarchy:")

    # Hiển thị cây hierarchy
    def print_hierarchy(hierarchy, level=0):
        for item_id, item in hierarchy.items():
            if item.get("parent_id") is None and level == 0:
                indent = "  " * level
                print(f"{indent}📁 {item['id']} ({item['level']}) - {item['title']}")
                print_children(hierarchy, item_id, level + 1)

    def print_children(hierarchy, parent_id, level):
        for item_id, item in hierarchy.items():
            if item.get("parent_id") == parent_id:
                indent = "  " * level
                print(f"{indent}📄 {item['id']} ({item['level']}) - {item['title']}")
                print_children(hierarchy, item_id, level + 1)

    print_hierarchy(hierarchy)

    print("\n📊 Chi tiết relationships:")
    for item_id, item in hierarchy.items():
        parent_id = item.get("parent_id", "None")
        children = item.get("children", [])
        hierarchy_path = " → ".join(item.get("hierarchy_path", []))
        print(
            f"🔗 {item_id}: parent={parent_id}, children={len(children)}, path={hierarchy_path}"
        )

    print("\n💡 Giải thích:")
    print("- parent_stack: stack theo dõi parents hiện tại")
    print("- Khi gặp element mới, pop stack đến khi tìm được parent phù hợp")
    print("- hierarchy_path: đường dẫn từ root đến element hiện tại")


def demo_5_cross_references():
    """
    DEMO 5: _extract_cross_references()
    Chức năng: Tìm tham chiếu đến các điều khác trong nội dung
    """
    print("\n\n🔗 DEMO 5: CROSS REFERENCES")
    print("=" * 50)

    parser = LegalDocumentParser()

    # Nội dung có cross-references
    content_with_refs = """
    Theo quy định tại Điều 3 của Bộ luật này và Khoản 2 Điều 5,
    việc áp dụng được thực hiện theo Chương II và Mục 1.
    Phần THỨ NHẤT quy định về các nguyên tắc chung.
    Căn cứ vào Điều 10, Khoản 3 và các quy định tại Chương V.
    """

    cross_refs = parser._extract_cross_references(content_with_refs)

    print("🔍 Cross-references tìm được:")
    for ref in cross_refs:
        print(f"  - {ref}")

    print(f"\n📊 Tổng số: {len(cross_refs)} references")

    print("\n💡 Giải thích:")
    print("- Sử dụng regex patterns để tìm tham chiếu")
    print("- Patterns: Điều X, Khoản Y, Chương Z, Mục W, Phần V")
    print("- Kết quả được deduplicate (loại bỏ trùng lặp)")


def demo_6_full_parsing():
    """
    DEMO 6: parse_document() - Full pipeline
    Chức năng: Demo quá trình parse hoàn chỉnh
    """
    print("\n\n📄 DEMO 6: FULL DOCUMENT PARSING")
    print("=" * 50)

    parser = LegalDocumentParser()

    # Load thật từ file
    data_path = Path("data/raw/bo_luat_dan_su_2015.txt")
    if not data_path.exists():
        print("⚠️ File data không tồn tại, sử dụng sample text")
        sample_text = """BỘ LUẬT DÂN SỰ 2015
PHẦN THỨ NHẤT: QUY ĐỊNH CHUNG
CHƯƠNG I: NHỮNG QUY ĐỊNH CHUNG
Điều 1. Phạm vi điều chỉnh
Bộ luật này quy định địa vị pháp lý của cá nhân, pháp nhân.
Điều 2. Công nhận quyền dân sự
1. Các quyền dân sự được công nhận theo Hiến pháp.
2. Quyền có thể bị hạn chế theo quy định của luật."""
    else:
        with open(data_path, "r", encoding="utf-8") as f:
            sample_text = f.read()[:2000]  # Chỉ lấy 2000 ký tự đầu

    # Parse document
    document = parser.parse_document(sample_text, "demo_bo_luat")

    print("📋 Kết quả parsing:")
    print(f"  - Document ID: {document.id}")
    print(f"  - Title: {document.title}")
    print(f"  - Type: {document.document_type}")
    print(f"  - Total provisions: {len(document.provisions)}")
    print(f"  - Structure elements: {len(document.structure)}")

    # Thống kê theo level
    level_counts = {}
    for provision in document.provisions:
        level = provision.level.value
        level_counts[level] = level_counts.get(level, 0) + 1

    print("\n📊 Thống kê theo level:")
    for level in ["phan", "chuong", "muc", "dieu", "khoan"]:
        count = level_counts.get(level, 0)
        print(f"  - {level.upper()}: {count}")

    # Hiển thị vài provisions đầu
    print("\n📝 Vài provisions đầu tiên:")
    for i, provision in enumerate(document.provisions[:3]):
        print(f"\n  {i+1}. {provision.id} ({provision.level.value})")
        print(f"     Title: {provision.title}")
        print(f"     Parent: {provision.parent_id}")
        print(
            f"     Path: {' → '.join(provision.hierarchy_path) if provision.hierarchy_path else 'None'}"
        )

    print("\n💡 Tổng kết:")
    print("- parse_document() là hàm chính gọi tất cả các hàm con")
    print("- Kết quả là LegalDocument object với đầy đủ thông tin")
    print("- Structure dict cho phép navigate theo hierarchy")
    print("- Provisions list chứa nội dung chi tiết từng điều khoản")


def main():
    """Chạy tất cả demos"""
    print("🎯 DEMO CHI TIẾT: LegalDocumentParser")
    print("=" * 60)
    print("Mục đích: Hiểu rõ từng hàm và cách hoạt động của parser")
    print("=" * 60)

    demo_1_pattern_matching()
    demo_2_hierarchy_relationships()
    demo_3_extract_provisions()
    demo_4_build_hierarchy()
    demo_5_cross_references()
    demo_6_full_parsing()

    print("\n" + "=" * 60)
    print("🎉 HOÀN THÀNH TẤT CẢ DEMOS!")
    print("=" * 60)


if __name__ == "__main__":
    main()
