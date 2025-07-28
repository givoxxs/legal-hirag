# scripts/process_legal_document.py
import json
import os
from pathlib import Path
from src.legal_hirag.core import (
    LegalDocumentParser,
    LegalStructureAnalyzer,
    LegalTextPreprocessor,
)


def process_legal_document(input_file: str, output_dir: str = "data/processed"):
    """Process a legal document from raw text to structured JSON"""

    # Initialize processors
    preprocessor = LegalTextPreprocessor()
    parser = LegalDocumentParser()
    analyzer = LegalStructureAnalyzer()

    # Read input file
    with open(input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print(f"📖 Processing document: {input_file}")

    # Step 1: Preprocess text
    print("🔧 Preprocessing text...")
    cleaned_text = preprocessor.preprocess(raw_text)

    # Step 2: Parse document structure
    print("📋 Parsing document structure...")
    document_id = Path(input_file).stem
    parsed_doc = parser.parse_to_json(cleaned_text, document_id)

    # Step 3: Analyze structure and add metadata
    print("🔍 Analyzing structure...")
    analyzed_doc = analyzer.analyze_structure(parsed_doc)

    # Step 4: Save outputs
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/json", exist_ok=True)
    os.makedirs(f"{output_dir}/metadata", exist_ok=True)

    # Save structured JSON
    json_output = f"{output_dir}/json/{document_id}.json"
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(analyzed_doc, f, ensure_ascii=False, indent=2)
    # Save metadata summary
    metadata_output = f"{output_dir}/metadata/{document_id}_metadata.json"
    metadata_summary = {
        "document_id": document_id,
        "title": analyzed_doc["title"],
        "statistics": analyzed_doc["statistics"],
        "processing_info": {
            "total_sections": len(analyzed_doc["structure"]),
            "hierarchy_levels": list(
                analyzed_doc["statistics"]["sections_by_level"].keys()
            ),
        },
    }

    with open(metadata_output, "w", encoding="utf-8") as f:
        json.dump(metadata_summary, f, ensure_ascii=False, indent=2)

    # Save cleaned text
    cleaned_output = f"{output_dir}/{document_id}_cleaned.txt"
    with open(cleaned_output, "w", encoding="utf-8") as f:
        f.write(cleaned_text)

    print(f"✅ Processing completed!")
    print(f"📄 Structured JSON: {json_output}")
    print(f"📊 Metadata: {metadata_output}")
    print(f"🧹 Cleaned text: {cleaned_output}")

    return analyzed_doc


def main():
    """Main function for command line usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Process legal document")
    parser.add_argument("input_file", help="Path to input legal document")
    parser.add_argument(
        "--output_dir",
        default="data/processed",
        help="Output directory (default: data/processed)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"❌ Input file not found: {args.input_file}")
        return

    try:
        result = process_legal_document(args.input_file, args.output_dir)
        print(f"\n📈 Statistics:")
        for level, count in result["statistics"]["sections_by_level"].items():
            print(f"  {level}: {count} sections")
        print(f"  Max depth: {result['statistics']['max_depth']}")
        print(f"  Cross-references: {result['statistics']['cross_references_count']}")

    except Exception as e:
        print(f"❌ Error processing document: {e}")


if __name__ == "__main__":
    main()
