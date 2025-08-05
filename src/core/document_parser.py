from typing import Dict, List, Optional, Tuple
import re
import json
from ..models.legal_schemas import LegalLevel, LegalProvision, LegalDocument


class LegalDocumentParser:
    """Parse Vietnamese legal documents into hierarchical structure"""

    def __init__(self):
        self.patterns = {
            "phan": r"PHẦN\s+([IVX]+|THỨ\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ]+):\s*(.+)",
            "chuong": r"CHƯƠNG\s+([IVX]+):\s*(.+)",
            "muc": r"MỤC\s+([IVX]+|\d+):\s*(.+)",  # Thêm pattern cho Mục
            "dieu": r"Điều\s+(\d+)\.\s*(.+)",
            "khoan": r"^(\d+)\.\s+(.+)",
        }
        self.hierarchy_order = [
            "phan",
            "chuong",
            "muc",
            "dieu",
            "khoan",
        ]  # Cập nhật thứ tự hierarchy

    def parse_document(self, text: str, document_id: str) -> LegalDocument:
        """Parse legal document text into structured format"""
        provisions = self._extract_provisions(text)

        # Gán document_id cho tất cả provisions
        for provision in provisions:
            provision.document_id = document_id

        structure = self._build_hierarchy(provisions)

        return LegalDocument(
            id=document_id,
            title=self._extract_title(text),
            document_type="legal_code",
            structure=structure,
            provisions=provisions,
        )

    def _extract_provisions(self, text: str) -> List[LegalProvision]:
        """Extract legal provisions from text"""
        provisions = []
        lines = text.split("\n")
        current_provision = None
        content_buffer = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match_result = self._match_legal_pattern(line)
            if match_result:
                # Save previous provision
                if current_provision:
                    current_provision.content = "\n".join(content_buffer).strip()
                    provisions.append(current_provision)

                # Start new provision
                level, number, title = match_result
                provision_id = f"{level}-{number}"

                current_provision = LegalProvision(
                    id=provision_id,
                    level=LegalLevel(level),
                    number=number,
                    title=title,
                    content="",
                    document_id="",
                )
                content_buffer = [line]
            else:
                if current_provision:
                    content_buffer.append(line)

        # Add last provision
        if current_provision:
            current_provision.content = "\n".join(content_buffer).strip()
            provisions.append(current_provision)

        return provisions

    def _match_legal_pattern(self, line: str) -> Optional[Tuple[str, str, str]]:
        """Match line against legal patterns"""
        for level, pattern in self.patterns.items():
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                if level in ["phan", "chuong", "muc"]:  # Thêm 'muc' vào xử lý
                    return level, match.group(1), match.group(2)
                elif level == "dieu":
                    return (
                        level,
                        match.group(1),
                        match.group(2) if len(match.groups()) > 1 else "",
                    )
                elif level == "khoan":
                    return level, match.group(1), match.group(2)
        return None

    def _build_hierarchy(self, provisions: List[LegalProvision]) -> Dict:
        """Build hierarchical structure from provisions"""
        hierarchy = {}
        parent_stack = []

        for provision in provisions:
            # Find appropriate parent
            while parent_stack and not self._is_child_of(
                provision.level.value, parent_stack[-1]["level"]
            ):
                parent_stack.pop()

            parent_id = parent_stack[-1]["id"] if parent_stack else None
            provision.parent_id = parent_id

            # Build hierarchy path
            if parent_stack:
                provision.hierarchy_path = parent_stack[-1]["hierarchy_path"] + [
                    provision.id
                ]
            else:
                provision.hierarchy_path = [provision.id]

            provision_data = {
                "id": provision.id,
                "level": provision.level.value,
                "number": provision.number,
                "title": provision.title,
                "parent_id": parent_id,
                "hierarchy_path": provision.hierarchy_path,
                "children": [],
            }

            # Add to parent's children
            if parent_id and parent_id in hierarchy:
                hierarchy[parent_id]["children"].append(provision.id)

            hierarchy[provision.id] = provision_data
            parent_stack.append(provision_data)

        return hierarchy

    def _is_child_of(self, child_level: str, parent_level: str) -> bool:
        """Check if child_level can be child of parent_level"""
        try:
            child_idx = self.hierarchy_order.index(child_level)
            parent_idx = self.hierarchy_order.index(parent_level)
            return child_idx > parent_idx
        except ValueError:
            return False

    def _extract_title(self, text: str) -> str:
        """Extract document title"""
        lines = text.split("\n")[:10]  # Tăng số dòng kiểm tra
        for line in lines:
            line = line.strip()
            if line and not self._match_legal_pattern(line):
                return line
        return "Legal Document"

    def _extract_cross_references(self, content: str) -> List[str]:
        """Extract cross-references from content"""
        cross_refs = []

        # Pattern để tìm tham chiếu đến các điều khác
        patterns = [
            r"Điều\s+(\d+)",
            r"Khoản\s+(\d+)",
            r"Chương\s+([IVX]+)",
            r"Mục\s+([IVX]+|\d+)",  # Thêm pattern cho Mục
            r"Phần\s+([IVX]+|THỨ\s+[A-Z]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    cross_refs.append(match[0])
                else:
                    cross_refs.append(match)

        return list(set(cross_refs))  # Remove duplicates
