#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.legal_hirag.core.document_parser import LegalDocumentParser
from src.legal_hirag.models.query_models import LegalQueryParam, LegalQueryMode
from src.legal_hirag.storage.storage_manager import LegalStorageManager
from src.legal_hirag.query.query_processor import LegalQueryProcessor
from src.legal_hirag.utils.config import load_config


async def demo_legal_hirag():
    """Demonstrate Legal HiRAG system capabilities"""

    print("🚀 Legal HiRAG System Demo")
    print("=" * 50)

    # Load configuration
    config = load_config("src/config/legal_config.yaml")

    # Initialize components
    storage = LegalStorageManager(config)
    query_processor = LegalQueryProcessor(storage, config["llm"])

    # Sample legal document
    sample_text = """  
BỘ LUẬT DÂN SỰ  
  
CHƯƠNG I: NHỮNG QUY ĐỊNH CHUNG  
  
Điều 1. Phạm vi điều chỉnh  
Bộ luật này quy định quyền, nghĩa vụ của cá nhân, pháp nhân trong quan hệ dân sự.  
  
Điều 2. Nguyên tắc bình đẳng  
Mọi cá nhân, pháp nhân đều bình đẳng trước pháp luật.  
  
CHƯƠNG II: CHỦ THỂ QUAN HỆ DÂN SỰ  
  
Điều 3. Cá nhân  
Cá nhân là chủ thể có năng lực pháp lý dân sự.  
  
Điều 4. Pháp nhân  
Pháp nhân là tổ chức có tư cách pháp lý độc lập.  
"""

    print("📄 Processing sample legal document...")

    # Parse document
    parser = LegalDocumentParser()
    document = parser.parse_document(sample_text, "demo_bo_luat_dan_su")

    print(f"   ✅ Parsed {len(document.provisions)} provisions")

    # Demo queries
    demo_queries = [
        {
            "question": "Ai có thể tham gia quan hệ dân sự?",
            "mode": LegalQueryMode.LOCAL,
            "description": "Local Query - Tìm thông tin cụ thể",
        },
        {
            "question": "Nguyên tắc cơ bản của pháp luật dân sự là gì?",
            "mode": LegalQueryMode.GLOBAL,
            "description": "Global Query - Tìm hiểu tổng quan",
        },
        {
            "question": "Mối quan hệ giữa cá nhân và pháp nhân trong pháp luật?",
            "mode": LegalQueryMode.BRIDGE,
            "description": "Bridge Query - Phân tích mối liên hệ",
        },
        {
            "question": "Tổng quan về chủ thể quan hệ dân sự?",
            "mode": LegalQueryMode.HIERARCHICAL,
            "description": "Hierarchical Query - Phân tích toàn diện",
        },
    ]

    print(f"\n🔍 Testing {len(demo_queries)} query modes...")

    for i, query_config in enumerate(demo_queries, 1):
        print(f"\n--- Query {i}: {query_config['description']} ---")
        print(f"❓ Question: {query_config['question']}")

        # Create query parameters
        params = LegalQueryParam(
            mode=query_config["mode"], top_k=10, response_type="Multiple Paragraphs"
        )

        try:
            # Process query
            result = await query_processor.process_query(
                query_config["question"], params
            )

            print(f"🤖 Answer ({result.mode}):")
            print(f"   {result.answer}")
            print(f"⏱️  Processing time: {result.processing_time:.2f}s")
            print(f"📊 Entities retrieved: {len(result.entities_retrieved)}")

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎉 Demo completed successfully!")

    # Cleanup
    await storage.close_connections()


if __name__ == "__main__":
    asyncio.run(demo_legal_hirag())
