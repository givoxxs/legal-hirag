# simple_view.py
import json

# Đọc file JSON
with open("tests/output/bo_luat_dan_su_2015_parsed.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== KẾT QUẢ PARSING ===")
print(f"Document: {data['document_info']['title']}")
print(f"Total provisions: {data['document_info']['total_provisions']}")

print("\nThống kê:")
for level, count in data["level_statistics"].items():
    print(f"- {level}: {count}")

print("\nVài provisions đầu:")
for i, p in enumerate(data["sample_provisions"][:3]):
    print(f"{i+1}. {p['id']} - {p['title']}")
    print(f"   Parent: {p['parent_id']}")
    print(f"   Path: {' -> '.join(p['hierarchy_path'])}")
    print()
