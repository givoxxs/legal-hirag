import re
from typing import List, Dict, Any, Optional, Tuple
from ..models.legal_schemas import LegalLevel


class VietnameseLegalParser:
    """Parser for Vietnamese legal document structures"""

    def __init__(self):
        self.level_patterns = {
            "phan": [
                r"PHẦN\s+([IVX]+|THỨ\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ]+):\s*(.+)",
                r"PHẦN\s+(\d+):\s*(.+)",
            ],
            "chuong": [r"CHƯƠNG\s+([IVX]+):\s*(.+)", r"CHƯƠNG\s+(\d+):\s*(.+)"],
            "muc": [r"MỤC\s+([IVX]+|\d+):\s*(.+)", r"Mục\s+([IVX]+|\d+):\s*(.+)"],
            "dieu": [r"Điều\s+(\d+)\.\s*(.+)", r"ĐIỀU\s+(\d+)\.\s*(.+)"],
            "khoan": [r"^(\d+)\.\s+(.+)", r"^([a-z])\)\s+(.+)", r"^([a-z])\.\s+(.+)"],
        }

        self.cross_ref_patterns = [
            r"Điều\s+(\d+)",
            r"Khoản\s+(\d+)",
            r"Chương\s+([IVX]+|\d+)",
            r"Mục\s+([IVX]+|\d+)",
            r"Phần\s+([IVX]+|THỨ\s+[A-Z]+|\d+)",
            r"theo\s+quy\s+định\s+tại\s+Điều\s+(\d+)",
            r"quy\s+định\s+tại\s+Khoản\s+(\d+)",
        ]

    def extract_legal_references(self, text: str) -> List[Dict[str, Any]]:
        """Extract legal references from text"""
        references = []

        for pattern in self.cross_ref_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                ref_type = self._determine_reference_type(pattern)
                references.append(
                    {
                        "type": ref_type,
                        "number": match.group(1),
                        "text": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        return references

    def _determine_reference_type(self, pattern: str) -> str:
        """Determine the type of legal reference"""
        if "Điều" in pattern:
            return "dieu"
        elif "Khoản" in pattern:
            return "khoan"
        elif "Chương" in pattern:
            return "chuong"
        elif "Mục" in pattern:
            return "muc"
        elif "Phần" in pattern:
            return "phan"
        return "unknown"

    def normalize_legal_text(self, text: str) -> str:
        """Normalize Vietnamese legal text"""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Normalize punctuation
        text = re.sub(r"\.{2,}", ".", text)
        text = re.sub(r",{2,}", ",", text)

        # Normalize Vietnamese characters
        text = self._normalize_vietnamese_chars(text)

        return text.strip()

    def _normalize_vietnamese_chars(self, text: str) -> str:
        """Normalize Vietnamese character variations"""
        # This could include normalization of different Vietnamese character encodings
        return text

    def extract_legal_entities_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract potential legal entities from text using patterns"""
        entities = []

        # Common legal entity patterns
        patterns = {
            "legal_concept": [
                r"quyền\s+[a-záàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]+",
                r"nghĩa\s+vụ\s+[a-záàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]+",
                r"nguyên\s+tắc\s+[a-záàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]+",
            ],
            "legal_entity": [
                r"cá\s+nhân",
                r"pháp\s+nhân",
                r"tổ\s+chức",
                r"cơ\s+quan\s+[a-záàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]+",
            ],
            "legal_procedure": [
                r"thủ\s+tục\s+[a-záàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]+",
                r"quy\s+trình\s+[a-záàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]+",
            ],
        }

        for entity_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities.append(
                        {
                            "text": match.group(0).strip(),
                            "type": entity_type,
                            "start": match.start(),
                            "end": match.end(),
                            "confidence": 0.7,  # Pattern-based confidence
                        }
                    )

        return entities
