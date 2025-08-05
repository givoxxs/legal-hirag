# view_parsing_results.py
"""
Script đơn giản để xem kết quả parsing
"""
import json
from pathlib import Path


def main():
    """Hiển thị kết quả parsing từ file JSON"""
    print("📊 KẾT QUẢ PARSING BỘ LUẬT DÂN SỰ 2015")
    print("=" * 60)

    # Đọc file JSON
    json_file = Path("tests/output/bo_luat_dan_su_2015_parsed.json")

    if not json_file.exists():
        print("❌ File JSON không tồn tại. Chạy test trước!")
        return

    print("📁 Đang đọc file JSON...")
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("✅ Đọc file thành công!")

    # Hiển thị thông tin document
    doc_info = data["document_info"]
    print(f"📄 Document: {doc_info['title']}")
    print(f"🆔 ID: {doc_info['id']}")
    print(f"📊 Tổng provisions: {doc_info['total_provisions']}")
    print(f"🌳 Structure elements: {doc_info['total_structure_elements']}")

    # Thống kê theo level
    print(f"\n📊 THỐNG KÊ THEO CẤP ĐỘ:")
    stats = data["level_statistics"]
    for level, count in stats.items():
        print(f"  - {level.upper()}: {count}")

    # Hiển thị sample provisions
    print(f"\n📝 MỘT SỐ PROVISIONS MẪU:")
    samples = data["sample_provisions"][:5]  # Chỉ 5 đầu tiên

    for i, provision in enumerate(samples, 1):
        print(f"\n  {i}. {provision['id']} ({provision['level'].upper()})")
        print(f"     Title: {provision['title']}")
        print(f"     Parent: {provision['parent_id'] or 'None'}")
        print(f"     Path: {' → '.join(provision['hierarchy_path'])}")
        print(f"     Content: {provision['content_preview']}")

    # Structure sample
    print(f"\n🌳 CẤU TRÚC HIERARCHY SAMPLE:")
    structure = data["structure_sample"]

    # Tìm root elements
    roots = [item for item in structure.values() if item.get("parent_id") is None]

    for root in roots[:1]:  # Chỉ 1 root đầu tiên
        print(f"\n📁 {root['id']} - {root['title']}")
        print(f"   Level: {root['level']}, Children: {len(root.get('children', []))}")

        # Hiển thị children
        for child_id in root.get("children", [])[:3]:  # 3 children đầu
            if child_id in structure:
                child = structure[child_id]
                print(f"   └── 📂 {child['id']} - {child['title']}")
                print(
                    f"       Level: {child['level']}, Children: {len(child.get('children', []))}"
                )

                # Grandchildren
                for grandchild_id in child.get("children", [])[:2]:  # 2 grandchildren
                    if grandchild_id in structure:
                        grandchild = structure[grandchild_id]
                        title = (
                            grandchild["title"][:50] + "..."
                            if len(grandchild["title"]) > 50
                            else grandchild["title"]
                        )
                        print(f"       └── 📄 {grandchild['id']} - {title}")

    print(f"\n✅ TỔNG KẾT:")
    print(f"  - Parser đã xử lý thành công {doc_info['total_provisions']} provisions")
    print(
        f"  - Tạo được cấu trúc hierarchy với {doc_info['total_structure_elements']} elements"
    )
    print(
        f"  - Bao gồm: {stats['phan']} Phần, {stats['chuong']} Chương, {stats['muc']} Mục, {stats['dieu']} Điều, {stats['khoan']} Khoản"
    )
    print(f"  - Kết quả đã được lưu trong {json_file}")


if __name__ == "__main__":
    main()
