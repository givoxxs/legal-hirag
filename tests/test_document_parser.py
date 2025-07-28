# tests/test_document_parser.py
import os
import sys
import json
from pathlib import Path

# Thêm thư mục gốc vào sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.legal_hirag.core.document_parser import LegalDocumentParser


def test_hierarchy_relationships():
    parser = LegalDocumentParser()
    assert parser._is_child_of("dieu", "chuong") == True
    assert parser._is_child_of("khoan", "dieu") == True
    assert parser._is_child_of("chuong", "phan") == True
    assert parser._is_child_of("muc", "chuong") == True
    assert parser._is_child_of("dieu", "muc") == True
    assert parser._is_child_of("phan", "chuong") == False
    assert parser._is_child_of("chuong", "dieu") == False
    print("Test hierarchy relationships: PASSED")


def test_parse_legal_document():
    """Test parsing legal document with real data"""

    # Đường dẫn đến file văn bản pháp luật
    data_path = (
        Path(__file__).parent.parent / "data" / "raw" / "bo_luat_dan_su_2015.txt"
    )

    # Kiểm tra xem file có tồn tại không
    if not data_path.exists():
        print(f"File không tồn tại: {data_path}")
        return

    # Đọc nội dung file
    with open(data_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Khởi tạo parser
    parser = LegalDocumentParser()

    # Parse văn bản
    result = parser.parse_to_json(content, "bo_luat_dan_su_2015")

    # Kiểm tra kết quả
    print(f"Tiêu đề văn bản: {result['title']}")
    print(f"Số lượng section: {len(result['sections'])}")

    # Phân loại các section theo cấp độ
    level_counts = {}
    for section in result["sections"]:
        level = section["level"]
        level_counts[level] = level_counts.get(level, 0) + 1

    print("Số lượng section theo cấp độ:")
    for level in ["phan", "chuong", "muc", "dieu", "khoan"]:
        count = level_counts.get(level, 0)
        print(f"  - {level}: {count}")

    # Kiểm tra xem các khoản có được gán đúng với điều không
    khoan_with_dieu = 0
    khoan_without_dieu = 0
    khoan_with_wrong_dieu = 0

    # Hiển thị thông tin chi tiết về khoản 1 và khoản 2 của điều 2
    dieu_2_found = False
    for section in result["structure"].values():
        if section["level"] == "dieu" and section["number"] == "2":
            dieu_2_found = True
            print(f"\nĐiều 2: {section['title']}")
            print(f"Children của điều 2: {section['children']}")

            # Kiểm tra các khoản của điều 2
            for child_id in section["children"]:
                child = result["structure"].get(child_id)
                if child:
                    print(f"  - {child_id}: {child['title'][:50]}...")

    if not dieu_2_found:
        print("Không tìm thấy Điều 2 trong structure")

    # Hiển thị nội dung của khoản 1 và khoản 2
    print("\nDanh sách các khoản 1 và 2:")
    for section in result["sections"]:
        if section["level"] == "khoan" and section["number"] in ["1", "2"]:
            print(
                f"Khoản {section['number']} - Parent: {section['parent_id']} - Title: {section['title'][:50]}..."
            )

    # Kiểm tra một số khoản cụ thể
    for section in result["sections"]:
        if section["level"] == "khoan":
            if section["parent_id"] and section["parent_id"].startswith("dieu-"):
                khoan_with_dieu += 1
            else:
                khoan_without_dieu += 1

    print(f"\nKhoản có điều cha: {khoan_with_dieu}")
    print(f"Khoản không có điều cha: {khoan_without_dieu}")

    # Lưu kết quả ra file JSON để kiểm tra
    output_path = Path(__file__).parent / "output" / "bo_luat_dan_su_2015.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Đã lưu kết quả vào: {output_path}")


if __name__ == "__main__":
    test_hierarchy_relationships()
    test_parse_legal_document()
