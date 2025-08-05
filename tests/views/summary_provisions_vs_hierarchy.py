# summary_provisions_vs_hierarchy.py
"""
TÓM TẮT: Provisions vs Hierarchy
"""


def main():
    print("🎯 TÓM TẮT: PROVISIONS vs HIERARCHY")
    print("=" * 50)

    print("📝 PROVISIONS (List[LegalProvision]):")
    print("  🎯 MỤC ĐÍCH: Lưu trữ NỘI DUNG đầy đủ")
    print("  📊 CẤU TRÚC: Danh sách tuần tự")
    print("  💾 DỮ LIỆU: Chứa toàn bộ text content")
    print("  🔍 TÌM KIẾM: Phải loop qua list (O(n))")
    print("  📈 BỘ NHỚ: Cao (do chứa content)")

    print("\n🌳 HIERARCHY (Dict[str, Dict]):")
    print("  🎯 MỤC ĐÍCH: Navigation và cấu trúc cây")
    print("  📊 CẤU TRÚC: Dictionary mapping")
    print("  💾 DỮ LIỆU: Chỉ metadata (không content)")
    print("  🔍 TÌM KIẾM: Direct access by key (O(1))")
    print("  📈 BỘ NHỚ: Thấp (chỉ metadata)")
    print("  👶 ĐẶC BIỆT: Có children list")

    print("\n🔄 VÍ DỤ THỰC TẾ:")
    print("┌────────────────────────────────────────────────────┐")
    print("│ PROVISIONS[0]:                                     │")
    print("│   id: 'dieu-1'                                    │")
    print("│   title: 'Phạm vi áp dụng'                        │")
    print("│   content: 'Điều 1. Phạm vi áp dụng\\nBộ luật...' │")
    print("│   parent_id: 'chuong-I'                           │")
    print("│   hierarchy_path: [...path array...]              │")
    print("└────────────────────────────────────────────────────┘")

    print("┌────────────────────────────────────────────────────┐")
    print("│ HIERARCHY['dieu-1']:                               │")
    print("│   {                                                │")
    print("│     'id': 'dieu-1',                               │")
    print("│     'title': 'Phạm vi áp dụng',                   │")
    print("│     'level': 'dieu',                              │")
    print("│     'parent_id': 'chuong-I',                      │")
    print("│     'children': [],                               │")
    print("│     'hierarchy_path': [...path array...]          │")
    print("│   }                                                │")
    print("│   # ❌ KHÔNG CÓ content field                     │")
    print("└────────────────────────────────────────────────────┘")

    print("\n🎯 KHI NÀO DÙNG CÁI NÀO?")
    print("📝 Dùng PROVISIONS khi:")
    print("  • Cần đọc nội dung đầy đủ")
    print("  • Entity extraction từ text")
    print("  • Text analysis, chunking")
    print("  • LLM processing")

    print("\n🌳 Dùng HIERARCHY khi:")
    print("  • Navigation UI (tree view)")
    print("  • Tìm children/parent nhanh")
    print("  • Tree traversal algorithms")
    print("  • Structure analysis")

    print("\n🚀 TRONG HIRAG SYSTEM:")
    print("📝 Provisions → Entity Extractor")
    print("📝 Provisions → Legal Chunker")
    print("📝 Provisions → Content Analysis")
    print("🌳 Hierarchy → Query Processor")
    print("🌳 Hierarchy → Context Builder")
    print("🌳 Hierarchy → Hierarchical Retrieval")

    print("\n💡 KẾT LUẬN:")
    print("• CẢ HAI đều cần thiết và bổ sung cho nhau")
    print("• Provisions = Content storage")
    print("• Hierarchy = Structure navigation")
    print("• Cùng phục vụ HiRAG system tối ưu!")


if __name__ == "__main__":
    main()

# python -m summary_provisions_vs_hierarchy
