# explain_provisions_vs_hierarchy.py
"""
Giải thích sự khác biệt giữa provisions và hierarchy
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.document_parser import LegalDocumentParser


def create_sample_document():
    """Tạo một văn bản mẫu nhỏ để demo"""
    sample_text = """BỘ LUẬT MẪU
PHẦN THỨ NHẤT: QUY ĐỊNH CHUNG  
CHƯƠNG I: NGUYÊN TẮC CƠ BẢN
Điều 1. Phạm vi áp dụng
Luật này áp dụng cho tất cả công dân Việt Nam.
Điều 2. Nguyên tắc cơ bản
1. Nguyên tắc bình đẳng trước pháp luật.
2. Nguyên tắc tôn trọng quyền con người.
CHƯƠNG II: QUYỀN VÀ NGHĨA VỤ
Điều 3. Quyền cơ bản
Mọi công dân đều có quyền được bảo vệ bởi pháp luật."""

    parser = LegalDocumentParser()
    return parser.parse_document(sample_text, "sample_law")


def explain_provisions(document):
    """Giải thích provisions"""
    print("📝 PROVISIONS (Danh sách tuần tự)")
    print("=" * 60)
    print("🎯 Mục đích: Lưu trữ NỘI DUNG CHI TIẾT của từng điều khoản")
    print("📊 Kiểu dữ liệu: List[LegalProvision] - danh sách tuần tự")
    print("🔍 Đặc điểm:")
    print("  - Mỗi element là một LegalProvision object")
    print("  - Chứa đầy đủ nội dung văn bản")
    print("  - Có thông tin parent_id và hierarchy_path")
    print("  - Thứ tự theo thứ tự xuất hiện trong văn bản")

    print(f"\n📋 Tổng số provisions: {len(document.provisions)}")

    print("\n🔍 Chi tiết từng provision:")
    for i, provision in enumerate(document.provisions):
        print(f"\n  {i+1}. PROVISION:")
        print(f"     📋 Object: LegalProvision")
        print(f"     🆔 ID: {provision.id}")
        print(f"     📊 Level: {provision.level.value}")
        print(f"     🔢 Number: {provision.number}")
        print(f"     🏷️ Title: {provision.title}")
        print(f"     👨‍👩‍👧‍👦 Parent ID: {provision.parent_id}")
        print(f"     🛤️ Hierarchy Path: {provision.hierarchy_path}")
        print(f"     📄 Content: {provision.content[:100]}...")
        print(f"     📏 Content Length: {len(provision.content)} chars")


def explain_hierarchy(document):
    """Giải thích hierarchy structure"""
    print("\n\n🌳 HIERARCHY/STRUCTURE (Cây phân cấp)")
    print("=" * 60)
    print("🎯 Mục đích: Biểu diễn CẤU TRÚC CÂY để navigation nhanh")
    print("📊 Kiểu dữ liệu: Dict[str, Dict] - dictionary ánh xạ")
    print("🔍 Đặc điểm:")
    print("  - Key: ID của element (string)")
    print("  - Value: Dictionary chứa metadata")
    print("  - Có children list để navigate xuống")
    print("  - Không chứa nội dung đầy đủ (chỉ metadata)")

    print(f"\n📋 Tổng số elements: {len(document.structure)}")

    print("\n🔍 Chi tiết từng element:")
    for element_id, element_data in document.structure.items():
        print(f"\n  📁 ELEMENT:")
        print(f"     📋 Object: Dictionary")
        print(f"     🆔 Key: '{element_id}'")
        print(f"     📊 Level: {element_data['level']}")
        print(f"     🏷️ Title: {element_data['title']}")
        print(f"     👨‍👩‍👧‍👦 Parent ID: {element_data['parent_id']}")
        print(f"     👶 Children: {element_data['children']}")
        print(f"     🛤️ Hierarchy Path: {element_data['hierarchy_path']}")
        print(f"     ❌ Content: KHÔNG CÓ (chỉ metadata)")


def compare_data_structures():
    """So sánh cấu trúc dữ liệu"""
    print("\n\n🔄 SO SÁNH CẤU TRÚC DỮ LIỆU")
    print("=" * 60)

    print("┌─────────────────┬─────────────────────┬─────────────────────┐")
    print("│ Khía cạnh       │ PROVISIONS          │ HIERARCHY           │")
    print("├─────────────────┼─────────────────────┼─────────────────────┤")
    print("│ Kiểu dữ liệu    │ List[LegalProvision]│ Dict[str, Dict]     │")
    print("│ Mục đích chính  │ Lưu nội dung        │ Navigation tree     │")
    print("│ Cấu trúc        │ Sequential list     │ Tree structure      │")
    print("│ Nội dung văn bản│ ✅ Đầy đủ          │ ❌ Không có         │")
    print("│ Metadata        │ ✅ Có               │ ✅ Có               │")
    print("│ Parent info     │ ✅ parent_id        │ ✅ parent_id        │")
    print("│ Children info   │ ❌ Không            │ ✅ children list    │")
    print("│ Hierarchy path  │ ✅ Có               │ ✅ Có               │")
    print("│ Search by ID    │ ❌ Phải loop        │ ✅ O(1) lookup     │")
    print("│ Memory usage    │ 🔴 Cao (content)    │ 🟢 Thấp (metadata) │")
    print("└─────────────────┴─────────────────────┴─────────────────────┘")


def demonstrate_use_cases(document):
    """Demo các use cases khác nhau"""
    print("\n\n🎯 USE CASES - KHI NÀO DÙNG CÁI NÀO?")
    print("=" * 60)

    print("📝 USE CASE 1: Tìm nội dung đầy đủ của Điều 2")
    print("👉 Dùng PROVISIONS (vì cần content)")
    for provision in document.provisions:
        if provision.id == "dieu-2":
            print(f"   ✅ Tìm thấy: {provision.title}")
            print(f"   📄 Content: {provision.content}")
            break

    print("\n🌳 USE CASE 2: Tìm tất cả children của Chương I")
    print("👉 Dùng HIERARCHY (vì cần children list)")
    chuong_1 = document.structure.get("chuong-I")
    if chuong_1:
        print(f"   ✅ Chương I có {len(chuong_1['children'])} children:")
        for child_id in chuong_1["children"]:
            child = document.structure[child_id]
            print(f"      - {child_id}: {child['title']}")

    print("\n🔍 USE CASE 3: Tìm path từ root đến Khoản 1")
    print("👉 Dùng CẢ HAI (provisions cho content, hierarchy cho navigation)")
    for provision in document.provisions:
        if provision.id == "khoan-1":
            print(f"   📍 Path: {' → '.join(provision.hierarchy_path)}")
            print(f"   📄 Content: {provision.content}")

            # Trace ngược parent chain
            print("   🔗 Parent chain:")
            current_id = provision.parent_id
            level = 1
            while current_id:
                parent = document.structure[current_id]
                print(f"      Level {level}: {parent['title']}")
                current_id = parent["parent_id"]
                level += 1
            break

    print("\n⚡ USE CASE 4: Performance comparison")
    print("👉 Tìm element by ID")

    import time

    # Test với provisions (phải loop)
    start = time.time()
    target_provision = None
    for provision in document.provisions:
        if provision.id == "dieu-2":
            target_provision = provision
            break
    provision_time = time.time() - start

    # Test với hierarchy (direct lookup)
    start = time.time()
    target_hierarchy = document.structure.get("dieu-2")
    hierarchy_time = time.time() - start

    print(f"   📊 Provisions lookup: {provision_time:.6f}s (O(n) - phải loop)")
    print(f"   📊 Hierarchy lookup: {hierarchy_time:.6f}s (O(1) - direct access)")
    # print(f"   ⚡ Hierarchy nhanh hơn: {provision_time/hierarchy_time:.1f}x")


def explain_why_need_both():
    """Giải thích tại sao cần cả hai"""
    print("\n\n❓ TẠI SAO CẦN CẢ HAI?")
    print("=" * 60)

    print("🎯 1. MỤC ĐÍCH KHÁC NHAU:")
    print("   📝 Provisions: Content storage (lưu trữ nội dung)")
    print("   🌳 Hierarchy: Structure navigation (điều hướng cấu trúc)")

    print("\n⚡ 2. PERFORMANCE KHÁC NHAU:")
    print("   📝 Provisions: Tốt cho sequential access, chậm cho lookup")
    print("   🌳 Hierarchy: Tốt cho random access, tree traversal")

    print("\n🔧 3. USE CASES BỔ SUNG:")
    print("   📝 Provisions phù hợp:")
    print("      - Đọc nội dung đầy đủ")
    print("      - Entity extraction")
    print("      - Text analysis")
    print("      - Content chunking")

    print("\n   🌳 Hierarchy phù hợp:")
    print("      - Navigation UI")
    print("      - Tree traversal")
    print("      - Parent-child queries")
    print("      - Structure analysis")

    print("\n💡 4. TRONG HIRAG SYSTEM:")
    print("   📝 Provisions → Entity Extractor → Legal entities")
    print("   📝 Provisions → Legal Chunker → Text chunks for vector DB")
    print("   🌳 Hierarchy → Query Processor → Hierarchical retrieval")
    print("   🌳 Hierarchy → Context Builder → Structure-aware context")


def main():
    """Hàm chính"""
    print("🎓 GIẢI THÍCH: PROVISIONS vs HIERARCHY")
    print("=" * 60)
    print("Mục đích: Hiểu sự khác biệt và lý do cần cả hai")
    print("=" * 60)

    # Tạo document mẫu
    document = create_sample_document()

    # Giải thích từng loại
    explain_provisions(document)
    explain_hierarchy(document)

    # So sánh
    compare_data_structures()

    # Demo use cases
    demonstrate_use_cases(document)

    # Giải thích tại sao cần cả hai
    explain_why_need_both()

    print("\n" + "=" * 60)
    print("🎉 KẾT LUẬN: Provisions + Hierarchy = Complete Solution!")
    print("📝 Provisions: Chi tiết nội dung")
    print("🌳 Hierarchy: Cấu trúc điều hướng")
    print("🚀 Cả hai cùng phục vụ HiRAG system một cách tối ưu!")
    print("=" * 60)


if __name__ == "__main__":
    main()

# python -m explain_provisions_vs_hierarchy
