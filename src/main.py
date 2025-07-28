#!/usr/bin/env python3
"""  
Legal HiRAG Main Application  
Entry point for the Legal HiRAG system  
"""

import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any

from .utils.config import load_config
from .storage.storage_manager import LegalStorageManager
from .query.query_processor import LegalQueryProcessor
from .core.document_parser import LegalDocumentParser
from .core.entity_extractor import LegalEntityExtractor
from .models.query_models import LegalQueryParam, LegalQueryMode


class LegalHiRAGSystem:
    """Main Legal HiRAG System"""

    def __init__(self, config_path: str = "src/config/legal_config.yaml"):
        self.config = load_config(config_path)
        self.storage = LegalStorageManager(self.config)
        self.query_processor = LegalQueryProcessor(self.storage, self.config["llm"])
        self.document_parser = LegalDocumentParser()
        self.entity_extractor = LegalEntityExtractor(self.config["llm"])

    async def process_document(self, file_path: str) -> bool:
        """Process a legal document"""
        try:
            # Read document
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            # Parse document structure
            document_id = Path(file_path).stem
            document = self.document_parser.parse_document(text, document_id)

            # Extract entities and relationships
            entities, relationships = await self.entity_extractor.extract_from_document(
                document
            )
            document.entities = entities
            document.relationships = relationships

            # Store in databases
            success = await self.storage.store_document(document)

            if success:
                print(f"✅ Successfully processed {file_path}")
                return True
            else:
                print(f"❌ Failed to process {file_path}")
                return False

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False

    async def query(self, question: str, mode: str = "hierarchical") -> str:
        """Query the legal knowledge base"""
        try:
            # Create query parameters
            params = LegalQueryParam(
                mode=LegalQueryMode(mode), top_k=20, response_type="Multiple Paragraphs"
            )

            # Process query
            result = await self.query_processor.process_query(question, params)

            return result.answer

        except Exception as e:
            print(f"❌ Error processing query: {e}")
            return "Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn."

    async def close(self):
        """Close system connections"""
        await self.storage.close_connections()


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Legal HiRAG System")
    parser.add_argument(
        "--config",
        default="src/config/legal_config.yaml",
        help="Configuration file path",
    )
    parser.add_argument("--process", help="Process a legal document")
    parser.add_argument("--query", help="Query the knowledge base")
    parser.add_argument(
        "--mode",
        default="hierarchical",
        choices=["hierarchical", "local", "global", "bridge", "provision"],
        help="Query mode",
    )

    args = parser.parse_args()

    # Initialize system
    system = LegalHiRAGSystem(args.config)

    try:
        if args.process:
            # Process document
            await system.process_document(args.process)
        elif args.query:
            # Query system
            response = await system.query(args.query, args.mode)
            print(f"\n🤖 Trả lời ({args.mode}):")
            print(response)
        else:
            # Interactive mode
            print("🚀 Legal HiRAG System - Interactive Mode")
            print("Nhập 'exit' để thoát")

            while True:
                question = input("\n❓ Câu hỏi: ")
                if question.lower() in ["exit", "quit", "thoát"]:
                    break

                response = await system.query(question)
                print(f"\n🤖 Trả lời:")
                print(response)

    finally:
        await system.close()


if __name__ == "__main__":
    asyncio.run(main())
