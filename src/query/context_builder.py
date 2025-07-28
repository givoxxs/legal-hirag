from typing import Dict, List, Any, Optional
import re
import asyncio
from ..models.query_models import LegalQueryParam
from ..storage.storage_manager import LegalStorageManager


class LegalContextBuilder:
    """Build query contexts for different legal query modes"""

    def __init__(self, storage_manager: LegalStorageManager):
        self.storage = storage_manager

    async def build_local_context(
        self, query: str, params: LegalQueryParam
    ) -> Dict[str, Any]:
        """Build local context focusing on specific entities and relationships"""

        # Query similar entities
        entities = await self.storage.query_similar_entities(
            query,
            top_k=params.top_k,
            filters=(
                {"entity_type": [et.value for et in params.entity_type_filter]}
                if params.entity_type_filter
                else None
            ),
        )

        # Get detailed entity information
        entity_details = []
        for entity in entities[:10]:  # Limit to top 10
            details = await self.storage.get_entity_details(entity["entity_name"])
            if details:
                entity_details.append(
                    {
                        **entity,
                        **details,
                        "rank": await self._get_entity_rank(entity["entity_name"]),
                    }
                )

        # Get related provisions
        provisions = []
        for entity in entities[:5]:  # Get provisions for top 5 entities
            entity_provisions = await self._get_provisions_for_entity(
                entity["entity_name"]
            )
            provisions.extend(entity_provisions)

        # Get relationships between entities
        relationships = await self._get_entity_relationships(entity_details)

        return {
            "entities": entity_details,
            "provisions": provisions[:10],  # Limit provisions
            "relationships": relationships,
            "context_type": "local",
        }

    async def build_global_context(
        self, query: str, params: LegalQueryParam
    ) -> Dict[str, Any]:
        """Build global context using community reports and high-level information"""

        # Get entities for community identification
        entities = await self.storage.query_similar_entities(query, top_k=20)

        # Get document structures for global context
        document_structures = []
        if params.document_filter:
            for doc_id in params.document_filter:
                structure = await self.storage.get_document_structure(doc_id)
                if structure:
                    document_structures.append(structure)

        # Get community reports (placeholder for HiRAG integration)
        community_reports = await self._get_community_reports(entities[:10])

        # Get background provisions from different document levels
        background_provisions = await self._get_background_provisions(query, params)

        return {
            "entities": entities[:5],  # High-level entities only
            "document_structures": document_structures,
            "community_reports": community_reports,
            "background_provisions": background_provisions,
            "context_type": "global",
        }

    async def build_bridge_context(
        self, query: str, params: LegalQueryParam
    ) -> Dict[str, Any]:
        """Build bridge context focusing on reasoning paths between entities"""

        # Get key entities
        entities = await self.storage.query_similar_entities(query, top_k=15)

        # Find reasoning paths between entities
        reasoning_paths = []
        bridge_relationships = []

        for i, entity1 in enumerate(entities[:3]):
            for entity2 in entities[i + 1 : i + 3]:
                path = await self._find_reasoning_path(
                    entity1["entity_name"], entity2["entity_name"]
                )
                if path:
                    reasoning_paths.append(path)

                # Get intermediate relationships
                bridge_rel = await self._get_bridge_relationships(
                    entity1["entity_name"], entity2["entity_name"]
                )
                if bridge_rel:
                    bridge_relationships.extend(bridge_rel)

        # Get supporting provisions for reasoning paths
        supporting_provisions = await self._get_supporting_provisions(reasoning_paths)

        return {
            "entities": entities[:8],
            "reasoning_paths": reasoning_paths,
            "bridge_relationships": bridge_relationships,
            "supporting_provisions": supporting_provisions,
            "context_type": "bridge",
        }

    async def build_hierarchical_context(
        self, query: str, params: LegalQueryParam
    ) -> Dict[str, Any]:
        """Build comprehensive hierarchical context combining all aspects"""

        # Combine local, global, and bridge contexts
        local_context = await self.build_local_context(query, params)
        global_context = await self.build_global_context(query, params)
        bridge_context = await self.build_bridge_context(query, params)

        # Merge and deduplicate entities
        all_entities = local_context["entities"] + global_context["entities"][:3]
        unique_entities = self._deduplicate_entities(all_entities)

        return {
            "entities": unique_entities,
            "provisions": local_context["provisions"],
            "document_structures": global_context["document_structures"],
            "reasoning_paths": bridge_context["reasoning_paths"],
            "relationships": local_context["relationships"],
            "community_reports": global_context["community_reports"],
            "context_type": "hierarchical",
        }

    async def build_provision_context(
        self, query: str, params: LegalQueryParam
    ) -> Dict[str, Any]:
        """Build context focusing on specific legal provisions"""

        # Extract provision references from query
        provision_refs = self._extract_provision_references(query)

        provisions = []
        for ref in provision_refs:
            # Get specific provisions by reference
            doc_provisions = await self._get_provisions_by_reference(
                ref, params.document_filter
            )
            provisions.extend(doc_provisions)

        # If no specific references, use entity-based search
        if not provisions:
            entities = await self.storage.query_similar_entities(query, top_k=10)
            for entity in entities[:5]:
                entity_provisions = await self._get_provisions_for_entity(
                    entity["entity_name"]
                )
                provisions.extend(entity_provisions)

        # Get cross-references and hierarchy context
        cross_references = await self._get_cross_references(provisions)
        hierarchy_context = await self._build_hierarchy_context(provisions)

        # Get related provisions through hierarchy
        related_provisions = await self._get_related_provisions_by_hierarchy(provisions)

        return {
            "provisions": provisions[:15],
            "cross_references": cross_references,
            "hierarchy_context": hierarchy_context,
            "related_provisions": related_provisions,
            "context_type": "provision",
        }

    # Helper methods implementation

    async def _get_provisions_for_entity(self, entity_name: str) -> List[Dict]:
        """Get provisions that mention a specific entity"""
        try:
            # Search through all documents for provisions containing the entity
            # This is a simplified implementation - in practice, you'd use full-text search
            all_documents = await self.storage.postgres.conn.fetch(
                "SELECT DISTINCT document_id FROM legal_chunks"
            )

            provisions = []
            for doc_row in all_documents:
                doc_provisions = await self.storage.get_provisions_by_document(
                    doc_row["document_id"]
                )
                for provision in doc_provisions:
                    if entity_name.lower() in provision.get("content", "").lower():
                        provisions.append(provision)

            return provisions[:5]  # Limit results

        except Exception as e:
            print(f"Error getting provisions for entity {entity_name}: {e}")
            return []

    async def _find_reasoning_path(self, entity1: str, entity2: str) -> Optional[Dict]:
        """Find reasoning path between two entities using Neo4j graph traversal"""
        try:
            # Use Neo4j to find shortest path between entities
            path_query = """  
            MATCH path = shortestPath((e1:LegalEntity {name: $entity1})-[*..5]-(e2:LegalEntity {name: $entity2}))  
            WHERE e1 <> e2  
            RETURN path  
            LIMIT 1  
            """

            async with self.storage.neo4j.driver.session() as session:
                result = await session.run(path_query, entity1=entity1, entity2=entity2)
                record = await result.single()

                if record and record["path"]:
                    path_nodes = [node["name"] for node in record["path"].nodes]
                    path_relationships = [
                        rel.type for rel in record["path"].relationships
                    ]

                    return {
                        "source": entity1,
                        "target": entity2,
                        "path_nodes": path_nodes,
                        "path_relationships": path_relationships,
                        "path_length": len(path_nodes) - 1,
                    }

            return None

        except Exception as e:
            print(f"Error finding reasoning path between {entity1} and {entity2}: {e}")
            return None

    def _extract_provision_references(self, query: str) -> List[str]:
        """Extract provision references from query text"""
        patterns = [
            r"Điều\s+(\d+)",
            r"Khoản\s+(\d+)",
            r"Chương\s+([IVX]+)",
            r"Mục\s+([IVX]+|\d+)",
            r"Phần\s+([IVX]+|THỨ\s+[A-Z]+)",
        ]

        references = []
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            references.extend(matches)

        return references

    async def _get_provisions_by_reference(
        self, reference: str, document_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """Get provisions by specific reference"""
        try:
            # Determine reference type and search accordingly
            if reference.isdigit():
                # Could be Điều or Khoản
                provisions = []

                # Search for Điều
                query = (
                    "SELECT * FROM legal_chunks WHERE level = 'dieu' AND number = $1"
                )
                if document_filter:
                    query += " AND document_id = ANY($2)"
                    results = await self.storage.postgres.conn.fetch(
                        query, reference, document_filter
                    )
                else:
                    results = await self.storage.postgres.conn.fetch(query, reference)

                provisions.extend([dict(row) for row in results])

                return provisions
            else:
                # Roman numerals for Chương, Mục, Phần
                for level in ["chuong", "muc", "phan"]:
                    query = f"SELECT * FROM legal_chunks WHERE level = '{level}' AND number = $1"
                    if document_filter:
                        query += " AND document_id = ANY($2)"
                        results = await self.storage.postgres.conn.fetch(
                            query, reference, document_filter
                        )
                    else:
                        results = await self.storage.postgres.conn.fetch(
                            query, reference
                        )

                    if results:
                        return [dict(row) for row in results]

                return []

        except Exception as e:
            print(f"Error getting provisions by reference {reference}: {e}")
            return []

    async def _get_cross_references(self, provisions: List[Dict]) -> List[str]:
        """Get cross-references from provisions"""
        cross_refs = []
        for provision in provisions:
            if "cross_references" in provision and provision["cross_references"]:
                cross_refs.extend(provision["cross_references"])
        return list(set(cross_refs))

    async def _build_hierarchy_context(self, provisions: List[Dict]) -> Dict[str, Any]:
        """Build hierarchy context from provisions"""
        hierarchy = {"phan": [], "chuong": [], "muc": [], "dieu": [], "khoan": []}

        for provision in provisions:
            level = provision.get("level", "unknown")
            if level in hierarchy:
                hierarchy[level].append(provision)

        # Add parent-child relationships
        hierarchy_with_relations = {}
        for level, items in hierarchy.items():
            if items:
                hierarchy_with_relations[level] = {
                    "items": items,
                    "count": len(items),
                    "parents": await self._get_parent_provisions(items),
                    "children": await self._get_child_provisions(items),
                }

        return hierarchy_with_relations

    async def _get_entity_rank(self, entity_name: str) -> int:
        """Get entity rank based on degree in knowledge graph"""
        try:
            async with self.storage.neo4j.driver.session() as session:
                result = await session.run(
                    "MATCH (e:LegalEntity {name: $name}) RETURN size((e)--()) as degree",
                    name=entity_name,
                )
                record = await result.single()
                return record["degree"] if record else 0
        except:
            return 0

    async def _get_entity_relationships(self, entities: List[Dict]) -> List[Dict]:
        """Get relationships between entities"""
        relationships = []
        try:
            entity_names = [e["entity_name"] for e in entities]

            async with self.storage.neo4j.driver.session() as session:
                result = await session.run(
                    """  
                    MATCH (e1:LegalEntity)-[r]->(e2:LegalEntity)  
                    WHERE e1.name IN $names AND e2.name IN $names  
                    RETURN e1.name as source, e2.name as target, type(r) as relation_type, r.description as description  
                """,
                    names=entity_names,
                )

                async for record in result:
                    relationships.append(
                        {
                            "source": record["source"],
                            "target": record["target"],
                            "type": record["relation_type"],
                            "description": record["description"],
                        }
                    )
        except Exception as e:
            print(f"Error getting entity relationships: {e}")

        return relationships

    # async def _get_community_reports(self, entities: List[Dict]) -> List[Dict]:
    #     """Get community reports for entities (placeholder for HiRAG integration)"""
    #     # This would integrate with HiRAG's community detection and reporting
    #     # For now, return empty list
    #     return []

    async def _get_community_reports(self, entities: List[Dict]) -> List[Dict]:
        """Get community reports for entities based on HiRAG community detection"""
        try:
            if not entities:
                return []

            # Get entity names for community lookup
            entity_names = [entity.get("entity_name", "") for entity in entities]

            # Find related communities from entities
            related_communities = []
            for entity in entities:
                # Get cluster information from Neo4j (similar to HiRAG approach)
                clusters = await self._get_entity_clusters(entity["entity_name"])
                if clusters:
                    related_communities.extend(clusters)

            # Remove duplicates and get unique community IDs
            unique_community_ids = list(
                set([str(cluster["cluster"]) for cluster in related_communities])
            )

            # Get community reports from storage
            community_reports = []
            for community_id in unique_community_ids[:5]:  # Limit to top 5
                report = await self._get_community_report_by_id(community_id)
                if report:
                    community_reports.append(report)

            # Sort by rating/importance
            community_reports.sort(key=lambda x: x.get("rating", 0), reverse=True)

            return community_reports

        except Exception as e:
            print(f"Error getting community reports: {e}")
            return []

    async def _get_entity_clusters(self, entity_name: str) -> List[Dict]:
        """Get cluster information for an entity from Neo4j"""
        try:
            async with self.storage.neo4j.driver.session() as session:
                result = await session.run(
                    """  
                    MATCH (e:LegalEntity {name: $name})  
                    RETURN e.clusters as clusters  
                """,
                    name=entity_name,
                )

                record = await result.single()
                if record and record["clusters"]:
                    import json

                    return json.loads(record["clusters"])

                return []

        except Exception as e:
            print(f"Error getting clusters for entity {entity_name}: {e}")
            return []

    async def _get_community_report_by_id(self, community_id: str) -> Optional[Dict]:
        """Get community report by ID from storage"""
        try:
            # This would query from community reports storage
            # For now, generate a mock report based on community entities

            # Get community entities from Neo4j
            community_entities = await self._get_community_entities(community_id)

            if not community_entities:
                return None

            # Generate basic community report
            report = {
                "id": community_id,
                "title": f"Cộng đồng pháp lý {community_id}",
                "summary": f"Cộng đồng bao gồm {len(community_entities)} thực thể pháp lý liên quan",
                "rating": min(5.0, len(community_entities) * 0.5),  # Simple rating
                "entities": community_entities,
                "report_string": self._format_community_report(community_entities),
            }

            return report

        except Exception as e:
            print(f"Error getting community report {community_id}: {e}")
            return None

    async def _get_community_entities(self, community_id: str) -> List[Dict]:
        """Get all entities in a community"""
        try:
            async with self.storage.neo4j.driver.session() as session:
                result = await session.run(
                    """  
                    MATCH (e:LegalEntity)  
                    WHERE e.clusters CONTAINS $community_id  
                    RETURN e.name as name, e.entity_type as type, e.description as description  
                    LIMIT 10  
                """,
                    community_id=community_id,
                )

                entities = []
                async for record in result:
                    entities.append(
                        {
                            "name": record["name"],
                            "type": record["type"],
                            "description": record["description"],
                        }
                    )

                return entities

        except Exception as e:
            print(f"Error getting community entities for {community_id}: {e}")
            return []

    def _format_community_report(self, entities: List[Dict]) -> str:
        """Format community report as markdown string"""
        if not entities:
            return ""

        # Group entities by type
        entity_groups = {}
        for entity in entities:
            entity_type = entity.get("type", "unknown")
            if entity_type not in entity_groups:
                entity_groups[entity_type] = []
            entity_groups[entity_type].append(entity)

        # Format report
        report_parts = []
        for entity_type, type_entities in entity_groups.items():
            report_parts.append(f"## {entity_type.title()}")
            for entity in type_entities:
                report_parts.append(f"- **{entity['name']}**: {entity['description']}")
            report_parts.append("")

        return "\n".join(report_parts)

    async def _get_background_provisions(
        self, query: str, params: LegalQueryParam
    ) -> List[Dict]:
        """Get background provisions for global context"""
        try:
            # Get provisions from higher hierarchy levels for context
            background_query = """  
            SELECT * FROM legal_chunks   
            WHERE level IN ('phan', 'chuong', 'muc')  
            ORDER BY level, number  
            LIMIT 5  
            """

            results = await self.storage.postgres.conn.fetch(background_query)
            return [dict(row) for row in results]
        except:
            return []

    async def _get_bridge_relationships(self, entity1: str, entity2: str) -> List[Dict]:
        """Get intermediate relationships between two entities"""
        try:
            async with self.storage.neo4j.driver.session() as session:
                result = await session.run(
                    """  
                    MATCH (e1:LegalEntity {name: $entity1})-[r1]->(intermediate:LegalEntity)-[r2]->(e2:LegalEntity {name: $entity2})  
                    RETURN intermediate.name as intermediate_entity,   
                           type(r1) as relation1_type, r1.description as relation1_desc,  
                           type(r2) as relation2_type, r2.description as relation2_desc  
                    LIMIT 5  
                """,
                    entity1=entity1,
                    entity2=entity2,
                )

                bridge_rels = []
                async for record in result:
                    bridge_rels.append(
                        {
                            "intermediate_entity": record["intermediate_entity"],
                            "relation1": {
                                "type": record["relation1_type"],
                                "description": record["relation1_desc"],
                            },
                            "relation2": {
                                "type": record["relation2_type"],
                                "description": record["relation2_desc"],
                            },
                        }
                    )

                return bridge_rels

        except Exception as e:
            print(f"Error getting bridge relationships: {e}")
            return []

    async def _get_supporting_provisions(
        self, reasoning_paths: List[Dict]
    ) -> List[Dict]:
        """Get provisions that support the reasoning paths"""
        supporting_provisions = []

        for path in reasoning_paths:
            if "path_nodes" in path:
                for node in path["path_nodes"]:
                    provisions = await self._get_provisions_for_entity(node)
                    supporting_provisions.extend(provisions[:2])  # Limit per entity

        # Remove duplicates
        seen_ids = set()
        unique_provisions = []
        for provision in supporting_provisions:
            if provision.get("id") not in seen_ids:
                seen_ids.add(provision.get("id"))
                unique_provisions.append(provision)

        return unique_provisions[:10]  # Overall limit

    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities based on entity_name"""
        seen_names = set()
        unique_entities = []

        for entity in entities:
            name = entity.get("entity_name", "")
            if name not in seen_names:
                seen_names.add(name)
                unique_entities.append(entity)

        return unique_entities

    async def _get_related_provisions_by_hierarchy(
        self, provisions: List[Dict]
    ) -> List[Dict]:
        """Get related provisions through hierarchical relationships"""
        related_provisions = []

        for provision in provisions:
            hierarchy_path = provision.get("hierarchy_path", [])

            # Get parent provisions
            if len(hierarchy_path) > 1:
                parent_id = hierarchy_path[-2]  # Get immediate parent
                parent_provision = await self._get_provision_by_id(parent_id)
                if parent_provision:
                    related_provisions.append(parent_provision)

            # Get sibling provisions (same parent)
            if provision.get("parent_id"):
                siblings = await self._get_child_provisions_by_parent(
                    provision["parent_id"]
                )
                related_provisions.extend(siblings[:3])  # Limit siblings

        return self._deduplicate_provisions(related_provisions)

    async def _get_provision_by_id(self, provision_id: str) -> Optional[Dict]:
        """Get a single provision by its ID"""
        try:
            result = await self.storage.postgres.conn.fetchrow(
                "SELECT * FROM legal_chunks WHERE id = $1", provision_id
            )
            return dict(result) if result else None
        except Exception as e:
            print(f"Error getting provision by ID {provision_id}: {e}")
            return None

    async def _get_child_provisions_by_parent(self, parent_id: str) -> List[Dict]:
        """Get child provisions by parent ID"""
        try:
            results = await self.storage.postgres.conn.fetch(
                "SELECT * FROM legal_chunks WHERE parent_id = $1 LIMIT 5", parent_id
            )
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error getting child provisions for parent {parent_id}: {e}")
            return []

    async def _get_parent_provisions(self, provisions: List[Dict]) -> List[Dict]:
        """Get parent provisions for a list of provisions"""
        parent_provisions = []

        for provision in provisions:
            if provision.get("parent_id"):
                parent = await self._get_provision_by_id(provision["parent_id"])
                if parent:
                    parent_provisions.append(parent)

        return self._deduplicate_provisions(parent_provisions)

    async def _get_child_provisions(self, provisions: List[Dict]) -> List[Dict]:
        """Get child provisions for a list of provisions"""
        child_provisions = []

        for provision in provisions:
            children = await self._get_child_provisions_by_parent(
                provision.get("id", "")
            )
            child_provisions.extend(children)

        return self._deduplicate_provisions(child_provisions)

    def _deduplicate_provisions(self, provisions: List[Dict]) -> List[Dict]:
        """Remove duplicate provisions based on ID"""
        seen_ids = set()
        unique_provisions = []

        for provision in provisions:
            provision_id = provision.get("id", "")
            if provision_id not in seen_ids:
                seen_ids.add(provision_id)
                unique_provisions.append(provision)

        return unique_provisions

    async def _get_provisions_with_full_text_search(
        self, query: str, limit: int = 10
    ) -> List[Dict]:
        """Get provisions using full-text search (PostgreSQL)"""
        try:
            # Use PostgreSQL full-text search if available
            search_query = """  
            SELECT *, ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as rank  
            FROM legal_chunks   
            WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)  
            ORDER BY rank DESC  
            LIMIT $2  
            """

            results = await self.storage.postgres.conn.fetch(search_query, query, limit)
            return [dict(row) for row in results]

        except Exception as e:
            print(f"Full-text search not available, falling back to simple search: {e}")
            # Fallback to simple LIKE search
            fallback_query = """  
            SELECT * FROM legal_chunks   
            WHERE content ILIKE $1 OR title ILIKE $1  
            LIMIT $2  
            """

            results = await self.storage.postgres.conn.fetch(
                fallback_query, f"%{query}%", limit
            )
            return [dict(row) for row in results]

    async def _calculate_context_relevance_score(
        self, context: Dict[str, Any], query: str
    ) -> float:
        """Calculate relevance score for the built context"""
        score = 0.0
        query_lower = query.lower()

        # Score based on entities
        if "entities" in context:
            for entity in context["entities"]:
                if query_lower in entity.get("name", "").lower():
                    score += 2.0
                if query_lower in entity.get("description", "").lower():
                    score += 1.0

        # Score based on provisions
        if "provisions" in context:
            for provision in context["provisions"]:
                if query_lower in provision.get("content", "").lower():
                    score += 1.5
                if query_lower in provision.get("title", "").lower():
                    score += 2.0

        # Normalize score
        total_items = len(context.get("entities", [])) + len(
            context.get("provisions", [])
        )
        return score / max(total_items, 1)
