from neo4j import AsyncGraphDatabase
from typing import Dict, List, Optional, Any
import asyncio
from ..models.legal_schemas import LegalEntity, LegalRelationship


class Neo4jAdapter:
    """Neo4j adapter for legal knowledge graph storage"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.driver = AsyncGraphDatabase.driver(
            config["uri"], auth=(config["user"], config["password"])
        )

    async def store_entity(self, entity: LegalEntity) -> bool:
        """Store legal entity in Neo4j"""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """  
                    MERGE (e:LegalEntity {name: $name})  
                    SET e.type = $type,  
                        e.description = $description,  
                        e.level = $level,  
                        e.source_id = $source_id,  
                        e.confidence_score = $confidence_score,  
                        e.updated_at = datetime()  
                    RETURN e  
                """,
                    name=entity.name,
                    type=entity.type.value,
                    description=entity.description,
                    level=entity.level.value if entity.level else None,
                    source_id=entity.source_id,
                    confidence_score=entity.confidence_score,
                )
                return await result.single() is not None
        except Exception as e:
            print(f"Error storing entity: {e}")
            return False

    async def store_relationship(self, relationship: LegalRelationship) -> bool:
        """Store legal relationship in Neo4j"""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """  
                    MATCH (source:LegalEntity {name: $source_entity})  
                    MATCH (target:LegalEntity {name: $target_entity})  
                    MERGE (source)-[r:RELATES {type: $rel_type}]->(target)  
                    SET r.description = $description,  
                        r.strength = $strength,  
                        r.source_id = $source_id,  
                        r.updated_at = datetime()  
                    RETURN r  
                """,
                    source_entity=relationship.source_entity,
                    target_entity=relationship.target_entity,
                    rel_type=relationship.relation_type.value,
                    description=relationship.description,
                    strength=relationship.strength,
                    source_id=relationship.source_id,
                )
                return await result.single() is not None
        except Exception as e:
            print(f"Error storing relationship: {e}")
            return False

    async def get_entity(self, entity_name: str) -> Optional[Dict]:
        """Get entity by name"""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """  
                    MATCH (e:LegalEntity {name: $name})  
                    RETURN e  
                """,
                    name=entity_name,
                )
                record = await result.single()
                if record:
                    return dict(record["e"])
                return None
        except Exception as e:
            print(f"Error getting entity: {e}")
            return None

    async def get_related_entities(
        self, entity_name: str, max_depth: int = 2
    ) -> List[Dict]:
        """Get entities related to given entity"""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    """  
                    MATCH (e:LegalEntity {name: $name})-[r*1..$max_depth]-(related:LegalEntity)  
                    RETURN DISTINCT related, r  
                    LIMIT 50  
                """,
                    name=entity_name,
                    max_depth=max_depth,
                )

                entities = []
                async for record in result:
                    entities.append(
                        {
                            "entity": dict(record["related"]),
                            "relationships": [dict(rel) for rel in record["r"]],
                        }
                    )
                return entities
        except Exception as e:
            print(f"Error getting related entities: {e}")
            return []

    async def close(self):
        """Close Neo4j connection"""
        await self.driver.close()
