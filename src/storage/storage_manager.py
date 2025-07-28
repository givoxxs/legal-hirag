from typing import Dict, List, Optional, Any
import asyncio
import time
from ..models.legal_schemas import LegalDocument, LegalEntity, LegalRelationship
from .neo4j_adapter import Neo4jAdapter
from .chroma_adapter import ChromaAdapter
from .postgres_adapter import PostgresAdapter


class LegalStorageManager:
    """Unified storage manager for legal documents"""

    def __init__(self, config: Dict[str, Any]):
        self.neo4j = Neo4jAdapter(config["databases"]["neo4j"])
        self.chroma = ChromaAdapter(config["databases"]["chromadb"])
        self.postgres = PostgresAdapter(config["databases"]["postgres"])

    async def store_document(self, document: LegalDocument) -> bool:
        """Store complete legal document across all storage systems"""
        try:
            # Store document metadata in PostgreSQL
            await self.postgres.store_document_metadata(document)

            # Store provisions in PostgreSQL
            for provision in document.provisions:
                await self.postgres.store_provision(provision)

            # Store entities in Neo4j and ChromaDB
            if document.entities:
                await self.store_entities(document.entities)

            # Store relationships in Neo4j
            if document.relationships:
                await self.store_relationships(document.relationships)

            return True

        except Exception as e:
            print(f"Error storing document {document.id}: {e}")
            return False

    async def store_entities(self, entities: List[LegalEntity]) -> bool:
        """Store entities in both Neo4j and ChromaDB"""
        try:
            # Store in Neo4j
            for entity in entities:
                await self.neo4j.store_entity(entity)

            # Prepare for vector storage
            entity_data = {}
            for entity in entities:
                entity_id = f"ent-{entity.name.lower().replace(' ', '_')}"
                entity_data[entity_id] = {
                    "content": f"{entity.name} {entity.description}",
                    "metadata": {
                        "entity_name": entity.name,
                        "entity_type": entity.type.value,
                        "level": entity.level.value if entity.level else "unknown",
                        "source_id": entity.source_id,
                        "confidence_score": entity.confidence_score or 0.0,
                    },
                }

            # Store in ChromaDB
            await self.chroma.upsert_entities(entity_data)
            return True

        except Exception as e:
            print(f"Error storing entities: {e}")
            return False

    async def store_relationships(self, relationships: List[LegalRelationship]) -> bool:
        """Store relationships in Neo4j"""
        try:
            for relationship in relationships:
                await self.neo4j.store_relationship(relationship)
            return True
        except Exception as e:
            print(f"Error storing relationships: {e}")
            return False

    async def query_similar_entities(
        self, query: str, top_k: int = 10, filters: Dict[str, Any] = None
    ) -> List[Dict]:
        """Query similar entities from ChromaDB"""
        return await self.chroma.query_similar(query, top_k, filters)

    async def get_entity_details(self, entity_name: str) -> Optional[Dict]:
        """Get detailed entity information from Neo4j"""
        return await self.neo4j.get_entity(entity_name)

    async def get_document_structure(self, doc_id: str) -> Optional[Dict]:
        """Get document structure from PostgreSQL"""
        return await self.postgres.get_document_structure(doc_id)

    async def get_provisions_by_document(self, doc_id: str) -> List[Dict]:
        """Get all provisions for a document"""
        return await self.postgres.get_provisions_by_document(doc_id)

    async def get_provisions_by_level(self, doc_id: str, level: str) -> List[Dict]:
        """Get provisions by specific level"""
        return await self.postgres.get_provisions_by_level(doc_id, level)

    async def close_connections(self):
        """Close all storage connections"""
        await self.neo4j.close()
        await self.postgres.close()
        # ChromaDB doesn't need explicit closing
