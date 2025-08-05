from typing import List, Tuple, Dict, Any
import asyncio
from ..models.legal_schemas import (
    LegalDocument,
    LegalEntity,
    LegalLevel,
    LegalRelationship,
    LegalEntityType,
    LegalRelationType,
)
from litellm import completion


class LegalEntityExtractor:
    """Extract legal entities and relationships from documents"""

    def __init__(self, llm_config: Dict[str, Any]):
        self.llm_config = llm_config
        self.entity_types = [
            "legal_concept",
            "legal_principle",
            "legal_entity",
            "legal_procedure",
            "legal_provision",
        ]

        self.entity_types_description = {
            "legal_concept": "Khái niệm pháp lý",
            "legal_principle": "Nguyên tắc pháp lý",
            "legal_entity": "Chủ thể pháp lý",
            "legal_procedure": "Thủ tục pháp lý",
            "legal_provision": "Điều khoản pháp luật",
        }

        # Legal-specific prompts
        self.entity_prompt_system = """  
Bạn là chuyên gia pháp luật. Từ văn bản pháp luật sau, hãy trích xuất:  
  
1. CÁC THỰC THỂ PHÁP LÝ với thông tin:  
    - entity_name: Tên thực thể (viết hoa chữ cái đầu)  
    - entity_type: Một trong các loại: {entity_types}  
    - entity_description: Mô tả chi tiết về thực thể  
  
2. CÁC MỐI QUAN HỆ giữa các thực thể:  
    - source_entity: Thực thể nguồn  
    - target_entity: Thực thể đích    
    - relationship_description: Mô tả mối quan hệ  
    - relationship_strength: Điểm số từ 0.0 đến 1.0  
  
Trả về kết quả theo format:  
("entity"<|>entity_name<|>entity_type<|>entity_description)  
("relationship"<|>source_entity<|>target_entity<|>relationship_description<|>relationship_strength)  
"""
        self.entity_prompt_user = """
Văn bản: {text}        
"""

    async def extract_from_document(
        self, document: LegalDocument
    ) -> Tuple[List[LegalEntity], List[LegalRelationship]]:
        """Extract entities and relationships from document provisions"""
        all_entities = []
        all_relationships = []

        for provision in document.provisions:
            entities, relationships = await self._extract_from_provision(
                provision, document.id
            )
            all_entities.extend(entities)
            all_relationships.extend(relationships)

        # Deduplicate entities
        unique_entities = self._deduplicate_entities(all_entities)

        return unique_entities, all_relationships

    async def _extract_from_provision(
        self, provision, document_id: str
    ) -> Tuple[List[LegalEntity], List[LegalRelationship]]:
        """Extract entities and relationships from a single provision"""

        entity_types_description = ""

        for k, v in self.entity_types_description.items():
            entity_types_description += f"{k}: {v}\n"

        prompt = [
            {
                "role": "system",
                "content": self.entity_prompt_system.format(
                    entity_types=entity_types_description
                ),
            },
            {
                "role": "user",
                "content": self.entity_prompt_user.format(text=provision.content),
            },
        ]

        response = await self._call_llm(prompt)

        # Parse response
        entities, relationships = self._parse_extraction_response(
            response, provision.id, provision.level
        )

        return entities, relationships

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API - implement based on your chosen LLM"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = completion(
                    model="gemini/gemini-2.0-flash",
                    messages=prompt,
                    api_key=self.llm_config.get("gemini").get("api_key"),
                )
                return response.choices[0].message.content

            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    return f"Lỗi LiteLLM sau {max_retries} lần thử: {str(e)}"
                print(f"Lần thử {retry_count} thất bại, đang thử lại...")
                await asyncio.sleep(1)  # Chờ 1 giây trước khi thử lại

    def _parse_extraction_response(
        self, response: str, source_id: str, level: LegalLevel
    ) -> Tuple[List[LegalEntity], List[LegalRelationship]]:
        """Parse LLM response to extract entities and relationships"""
        entities = []
        relationships = []

        lines = response.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('("entity"'):
                entity = self._parse_entity_line(line, source_id, level)
                if entity:
                    entities.append(entity)
            elif line.startswith('("relationship"'):
                relationship = self._parse_relationship_line(line, source_id)
                if relationship:
                    relationships.append(relationship)

        return entities, relationships

    def _parse_entity_line(
        self, line: str, source_id: str, level: LegalLevel
    ) -> LegalEntity:
        """Parse entity line from LLM response"""
        try:
            # Extract content between parentheses
            content = line[line.find("(") + 1 : line.rfind(")")]
            parts = content.split("<|>")

            if len(parts) >= 4:
                return LegalEntity(
                    name=parts[1].strip(),
                    type=LegalEntityType(
                        parts[2].strip().lower().replace("'", "").replace('"', "")
                    ),
                    description=parts[3].strip(),
                    source_id=source_id,
                    confidence_score=0.8,
                    level=level,
                )
        except Exception as e:
            print(f"Error parsing entity line: {line}, error: {e}")

        return None

    def _parse_relationship_line(self, line: str, source_id: str) -> LegalRelationship:
        """Parse relationship line from LLM response"""
        try:
            content = line[line.find("(") + 1 : line.rfind(")")]
            parts = content.split("<|>")

            if len(parts) >= 5:
                return LegalRelationship(
                    source_entity=parts[1].strip(),
                    target_entity=parts[2].strip(),
                    relation_type=LegalRelationType.RELATES_TO,  # Default type
                    description=parts[3].strip(),
                    strength=float(parts[4].strip()),
                    source_id=source_id,
                )
        except Exception as e:
            print(f"Error parsing relationship line: {line}, error: {e}")

        return None

    def _deduplicate_entities(self, entities: List[LegalEntity]) -> List[LegalEntity]:
        """Remove duplicate entities based on name"""
        seen_names = set()
        unique_entities = []

        for entity in entities:
            if entity.name not in seen_names:
                seen_names.add(entity.name)
                unique_entities.append(entity)

        return unique_entities
