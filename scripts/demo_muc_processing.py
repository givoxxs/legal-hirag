#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.legal_hirag.core.document_parser import LegalDocumentParser
from src.legal_hirag.models.legal_schemas import LegalLevel


async def demo_muc_processing():
    """Demo processing documents with Mục level"""

    print("🚀 Demo: Legal Document Processing with Mục Level")
    print("=" * 60)

    # Sample text with Mục
    sample_text = """  
BỘ LUẬT DÂN SỰ  
  
PHẦN THỨ NHẤT: QUY ĐỊNH CHUNG  
  
CHƯƠNG I: NHỮNG QUY ĐỊNH CHUNG  
  
MỤC 1: PHẠM VI ĐIỀU CHỈNH VÀ NGUYÊN TẮC  
  
Điều 1. Phạm vi điều chỉnh  
Bộ luật này quy định quyền, nghĩa vụ của cá nhân, pháp nhân trong quan hệ dân sự.  
  
Điều 2. Nguyên tắc bình đẳng  
Mọi cá nhân, pháp nhân đều bình đẳng trước pháp luật.  
  
MỤC 2: CHỦ THỂ QUAN HỆ DÂN SỰ  
  
Điều 3. Cá nhân  
Cá nhân là chủ thể có năng lực pháp lý dân sự.  
1. Mọi cá nhân đều có năng lực pháp lý dân sự như nhau.  
2. Năng lực pháp lý dân sự của cá nhân được thành lập từ khi sinh ra.  
  
Điều 4. Pháp nhân  
Pháp nhân là tổ chức có tư cách pháp lý độc lập.  
"""

    # Parse document
    parser = LegalDocumentParser()
    document = parser.parse_document(sample_text, "demo_muc_doc")

    print(f"📄 Document: {document.title}")
    print(f"📊 Total provisions: {len(document.provisions)}")

    # Analyze by levels
    level_counts = {}
    for provision in document.provisions:
        level = provision.level.value
        level_counts[level] = level_counts.get(level, 0) + 1

    print(f"\n📋 Provisions by level:")
    for level in ["phan", "chuong", "muc", "dieu", "khoan"]:
        count = level_counts.get(level, 0)
        if count > 0:
            print(f"   {level.upper()}: {count}")

    # Show hierarchy structure
    print(f"\n🌳 Hierarchy Structure:")
    for provision in document.provisions:
        indent = "  " * (len(provision.hierarchy_path) - 1)
        print(f"{indent}{provision.id}: {provision.title}")

    # Show Mục details
    muc_provisions = [p for p in document.provisions if p.level == LegalLevel.MUC]
    print(f"\n📑 Mục Details:")
    for muc in muc_provisions:
        print(f"   {muc.id}: {muc.title}")

        # Find children Điều
        children_dieu = [
            p
            for p in document.provisions
            if p.level == LegalLevel.DIEU and muc.id in p.hierarchy_path
        ]
        for dieu in children_dieu:
            print(f"     └─ {dieu.id}: {dieu.title}")

    print(f"\n✅ Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(demo_muc_processing())
