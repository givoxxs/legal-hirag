import pytest
from src.legal_hirag.core.document_parser import LegalDocumentParser
from src.legal_hirag.models.legal_schemas import LegalLevel


def test_muc_parsing():
    """Test parsing documents with Mục level"""

    sample_text = """  
BỘ LUẬT DÂN SỰ  
  
PHẦN THỨ NHẤT: QUY ĐỊNH CHUNG  
  
CHƯƠNG I: NHỮNG QUY ĐỊNH CHUNG  
  
MỤC 1: PHẠM VI ĐIỀU CHỈNH  
  
Điều 1. Phạm vi điều chỉnh  
Bộ luật này quy định quyền, nghĩa vụ của cá nhân, pháp nhân trong quan hệ dân sự.  
  
Điều 2. Nguyên tắc bình đẳng  
Mọi cá nhân, pháp nhân đều bình đẳng trước pháp luật.  
  
MỤC 2: CHỦ THỂ QUAN HỆ DÂN SỰ  
  
Điều 3. Cá nhân  
Cá nhân là chủ thể có năng lực pháp lý dân sự.  
  
Điều 4. Pháp nhân  
Pháp nhân là tổ chức có tư cách pháp lý độc lập.  
"""

    parser = LegalDocumentParser()
    document = parser.parse_document(sample_text, "test_muc_doc")

    # Verify Mục provisions are parsed
    muc_provisions = [p for p in document.provisions if p.level == LegalLevel.MUC]
    assert len(muc_provisions) == 2

    # Verify hierarchy
    muc1 = next(p for p in muc_provisions if p.number == "1")
    assert muc1.title == "PHẠM VI ĐIỀU CHỈNH"

    # Verify Điều under Mục
    dieu_provisions = [p for p in document.provisions if p.level == LegalLevel.DIEU]
    dieu1 = next(p for p in dieu_provisions if p.number == "1")

    # Check hierarchy path includes Mục
    assert "muc-1" in dieu1.hierarchy_path

    print("✅ Mục parsing test passed")


def test_hierarchy_with_muc():
    """Test complete hierarchy with Mục level"""

    parser = LegalDocumentParser()

    # Test hierarchy order
    assert parser._is_child_of("muc", "chuong") == True
    assert parser._is_child_of("dieu", "muc") == True
    assert parser._is_child_of("khoan", "dieu") == True
    assert parser._is_child_of("chuong", "muc") == False

    print("✅ Hierarchy with Mục test passed")


if __name__ == "__main__":
    test_muc_parsing()
    test_hierarchy_with_muc()
