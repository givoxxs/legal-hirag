#!/usr/bin/env python3
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.document_parser import LegalDocumentParser
from src.core.entity_extractor import LegalEntityExtractor
from src.storage.storage_manager import LegalStorageManager
from src.utils.config import load_config


async def process_legal_document(
    file_path: str, config_path: str = "src/config/legal_config.yaml"
):
    """Process a single legal document through the complete pipeline"""

    print(f"🚀 Processing legal document: {file_path}")

    # Load configuration
    config = load_config(config_path)

    # Initialize components
    parser = LegalDocumentParser()
    extractor = LegalEntityExtractor(config["llm"])
    storage = LegalStorageManager(config)

    try:
        # Read document
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Parse document structure
        print("📋 Parsing document structure...")
        document_id = Path(file_path).stem
        document = parser.parse_document(text, document_id)
        print(f"   ✅ Found {len(document.provisions)} provisions")

        # Extract entities and relationships
        print("🔍 Extracting entities and relationships...")
        entities, relationships = await extractor.extract_from_document(document)
        document.entities = entities
        document.relationships = relationships
        print(
            f"   ✅ Extracted {len(entities)} entities, {len(relationships)} relationships"
        )

        # Store in databases
        print("💾 Storing in databases...")
        success = await storage.store_document(document)

        if success:
            print(f"✅ Successfully processed {file_path}")
            print(f"   📊 Document: {document.title}")
            print(f"   📄 Provisions: {len(document.provisions)}")
            print(f"   🏷️ Entities: {len(entities)}")
            print(f"   🔗 Relationships: {len(relationships)}")
        else:
            print(f"❌ Failed to process {file_path}")

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await storage.close_connections()


async def main():
    """Main function for batch processing"""
    import argparse

    parser = argparse.ArgumentParser(description="Process legal documents")
    parser.add_argument("input_path", help="Path to legal document or directory")
    parser.add_argument(
        "--config",
        default="src/config/legal_config.yaml",
        help="Configuration file path",
    )

    args = parser.parse_args()

    input_path = Path(args.input_path)

    if input_path.is_file():
        # Process single file
        await process_legal_document(str(input_path), args.config)
    elif input_path.is_dir():
        # Process all .txt files in directory
        txt_files = list(input_path.glob("*.txt"))
        print(f"📁 Found {len(txt_files)} legal documents to process")

        for txt_file in txt_files:
            await process_legal_document(str(txt_file), args.config)
            print()  # Add spacing between documents
    else:
        print(f"❌ Invalid input path: {input_path}")


if __name__ == "__main__":
    asyncio.run(main())
