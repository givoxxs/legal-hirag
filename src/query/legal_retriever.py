from typing import List, Dict, Any, Optional
from ..storage.storage_manager import LegalStorageManager
from ..models.query_models import LegalQueryParam
from ..models.legal_schemas import LegalLevel, LegalEntityType


class LegalRetriever:
    """Legal-specific retrieval for HiRAG queries"""

    def __init__(self, storage_manager: LegalStorageManager):
        self.storage = storage_manager

    async def retrieve_entities(
        self, query: str, params: LegalQueryParam
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant legal entities"""

        # Build filters based on parameters
        filters = {}
        if params.entity_type_filter:
            filters["entity_type"] = [et.value for et in params.entity_type_filter]
        if params.provision_level_filter:
            filters["level"] = [level.value for level in params.provision_level_filter]

        # Query similar entities
        entities = await self.storage.query_similar_entities(
            query, top_k=params.top_k, filters=filters
        )

        # Enhance with detailed information
        enhanced_entities = []
        for entity in entities:
            details = await self.storage.get_entity_details(entity["entity_name"])
            if details:
                enhanced_entities.append({**entity, **details})
            else:
                enhanced_entities.append(entity)

        return enhanced_entities

    async def retrieve_provisions(
        self, query: str, params: LegalQueryParam
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant legal provisions"""

        provisions = []

        # If document filter is specified
        if params.document_filter:
            for doc_id in params.document_filter:
                if params.provision_level_filter:
                    # Get provisions by specific levels
                    for level in params.provision_level_filter:
                        level_provisions = await self.storage.get_provisions_by_level(
                            doc_id, level.value
                        )
                        provisions.extend(level_provisions)
                else:
                    # Get all provisions for document
                    doc_provisions = await self.storage.get_provisions_by_document(
                        doc_id
                    )
                    provisions.extend(doc_provisions)

        # Filter and rank provisions by relevance
        if provisions:
            provisions = self._rank_provisions_by_relevance(query, provisions)

        return provisions[: params.top_k]

    async def retrieve_cross_references(
        self, entity_names: List[str]
    ) -> Dict[str, List[str]]:
        """Retrieve cross-references for entities"""

        cross_refs = {}
        for entity_name in entity_names:
            # Get related entities from graph
            related = await self.storage.neo4j.get_related_entities(entity_name)
            cross_refs[entity_name] = [rel["entity"]["name"] for rel in related]

        return cross_refs

    def _rank_provisions_by_relevance(
        self, query: str, provisions: List[Dict]
    ) -> List[Dict]:
        """Rank provisions by relevance to query"""
        # Simple text-based ranking - could be enhanced with embeddings
        query_lower = query.lower()

        for provision in provisions:
            content = provision.get("content", "").lower()
            title = provision.get("title", "").lower()

            # Calculate relevance score
            content_score = content.count(query_lower)
            title_score = (
                title.count(query_lower) * 2
            )  # Title matches are more important

            provision["relevance_score"] = content_score + title_score

        # Sort by relevance score descending
        return sorted(
            provisions, key=lambda x: x.get("relevance_score", 0), reverse=True
        )

    async def retrieve_hierarchy_context(self, provision_id: str) -> Dict[str, Any]:
        """Retrieve hierarchical context for a provision"""
        # This would get parent and child provisions in the hierarchy
        return {}

    async def retrieve_hierarchy_context(self, provision_id: str) -> Dict[str, Any]:
        """Retrieve hierarchical context for a provision"""
        try:
            # Get the target provision
            target_provision = await self._get_provision_by_id(provision_id)
            if not target_provision:
                return {}

            # Get hierarchy path and build context
            hierarchy_path = target_provision.get("hierarchy_path", [])

            # Get parent provisions (ancestors)
            parent_provisions = await self._get_parent_provisions_chain(provision_id)

            # Get child provisions (descendants)
            child_provisions = await self._get_child_provisions_tree(provision_id)

            # Get sibling provisions (same level, same parent)
            sibling_provisions = await self._get_sibling_provisions(provision_id)

            # Get cross-referenced provisions
            cross_referenced = await self._get_cross_referenced_provisions(
                target_provision
            )

            # Build hierarchical structure
            hierarchy_structure = await self._build_provision_hierarchy_tree(
                target_provision
            )

            return {
                "target_provision": target_provision,
                "hierarchy_path": hierarchy_path,
                "parent_provisions": parent_provisions,
                "child_provisions": child_provisions,
                "sibling_provisions": sibling_provisions,
                "cross_referenced": cross_referenced,
                "hierarchy_structure": hierarchy_structure,
                "context_type": "hierarchical_provision",
            }

        except Exception as e:
            print(f"Error retrieving hierarchy context for {provision_id}: {e}")
            return {}

    async def _get_provision_by_id(self, provision_id: str) -> Optional[Dict]:
        """Get a single provision by its ID"""
        try:
            result = await self.storage.postgres.conn.fetchrow(
                "SELECT * FROM legal_chunks WHERE id = $1", provision_id
            )
            return dict(result) if result else None
        except Exception as e:
            print(f"Error getting provision {provision_id}: {e}")
            return None

    async def _get_parent_provisions_chain(self, provision_id: str) -> List[Dict]:
        """Get all parent provisions in the hierarchy chain"""
        try:
            # Get the provision's hierarchy path
            provision = await self._get_provision_by_id(provision_id)
            if not provision or not provision.get("hierarchy_path"):
                return []

            hierarchy_path = provision["hierarchy_path"]
            parent_provisions = []

            # Get all parents in the chain (excluding self)
            for parent_id in hierarchy_path[:-1]:
                parent = await self._get_provision_by_id(parent_id)
                if parent:
                    parent_provisions.append(parent)

            return parent_provisions

        except Exception as e:
            print(f"Error getting parent chain for {provision_id}: {e}")
            return []

    async def _get_child_provisions_tree(self, provision_id: str) -> List[Dict]:
        """Get all child provisions recursively"""
        try:
            # Get direct children
            direct_children = await self.storage.postgres.conn.fetch(
                "SELECT * FROM legal_chunks WHERE parent_id = $1 ORDER BY number",
                provision_id,
            )

            children_tree = []
            for child in direct_children:
                child_dict = dict(child)

                # Recursively get grandchildren
                grandchildren = await self._get_child_provisions_tree(child["id"])
                if grandchildren:
                    child_dict["children"] = grandchildren

                children_tree.append(child_dict)

            return children_tree

        except Exception as e:
            print(f"Error getting children for {provision_id}: {e}")
            return []

    async def _get_sibling_provisions(self, provision_id: str) -> List[Dict]:
        """Get sibling provisions (same parent, same level)"""
        try:
            provision = await self._get_provision_by_id(provision_id)
            if not provision or not provision.get("parent_id"):
                return []

            # Get all siblings with same parent
            siblings = await self.storage.postgres.conn.fetch(
                """  
                SELECT * FROM legal_chunks   
                WHERE parent_id = $1 AND id != $2   
                ORDER BY number  
            """,
                provision["parent_id"],
                provision_id,
            )

            return [dict(sibling) for sibling in siblings]

        except Exception as e:
            print(f"Error getting siblings for {provision_id}: {e}")
            return []

    async def _get_cross_referenced_provisions(self, provision: Dict) -> List[Dict]:
        """Get provisions that are cross-referenced by this provision"""
        try:
            cross_refs = provision.get("cross_references", [])
            if not cross_refs:
                return []

            referenced_provisions = []
            for ref in cross_refs:
                # Try to find provisions matching the reference
                ref_provisions = await self._find_provisions_by_reference(
                    ref, provision.get("document_id")
                )
                referenced_provisions.extend(ref_provisions)

            return referenced_provisions[:10]  # Limit results

        except Exception as e:
            print(f"Error getting cross-references: {e}")
            return []

    async def _find_provisions_by_reference(
        self, reference: str, document_id: str
    ) -> List[Dict]:
        """Find provisions by reference string (e.g., 'Điều 5', 'Khoản 2')"""
        try:
            # Parse reference to extract level and number
            import re

            patterns = {
                "dieu": r"Điều\s+(\d+)",
                "khoan": r"Khoản\s+(\d+)",
                "chuong": r"Chương\s+([IVX]+)",
                "muc": r"Mục\s+([IVX]+|\d+)",
                "phan": r"Phần\s+([IVX]+|THỨ\s+[A-Z]+)",
            }

            for level, pattern in patterns.items():
                match = re.search(pattern, reference, re.IGNORECASE)
                if match:
                    number = match.group(1)

                    # Query provisions with matching level and number
                    results = await self.storage.postgres.conn.fetch(
                        """  
                        SELECT * FROM legal_chunks   
                        WHERE level = $1 AND number = $2 AND document_id = $3  
                    """,
                        level,
                        number,
                        document_id,
                    )

                    return [dict(row) for row in results]

            return []

        except Exception as e:
            print(f"Error finding provisions by reference {reference}: {e}")
            return []

    async def _build_provision_hierarchy_tree(
        self, target_provision: Dict
    ) -> Dict[str, Any]:
        """Build a tree structure showing the provision's position in hierarchy"""
        try:
            document_id = target_provision.get("document_id")
            if not document_id:
                return {}

            # Get document structure
            doc_structure = await self.storage.get_document_structure(document_id)
            if not doc_structure:
                return {}

            # Find the target provision's position in the structure
            hierarchy_path = target_provision.get("hierarchy_path", [])

            # Build focused tree around the target provision
            focused_tree = {}
            current_level = focused_tree

            for i, provision_id in enumerate(hierarchy_path):
                provision = await self._get_provision_by_id(provision_id)
                if provision:
                    level_key = f"{provision['level']}-{provision['number']}"
                    current_level[level_key] = {
                        "id": provision["id"],
                        "level": provision["level"],
                        "number": provision["number"],
                        "title": provision.get("title", ""),
                        "is_target": provision["id"] == target_provision["id"],
                        "children": {},
                    }
                    current_level = current_level[level_key]["children"]

            return focused_tree

        except Exception as e:
            print(f"Error building hierarchy tree: {e}")
            return {}
