import chromadb
from typing import Dict, List, Optional, Any
import asyncio


class ChromaAdapter:
    """ChromaDB adapter for legal entity embeddings"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Initialize client based on config
        if "host" in config and config.get("host") != "localhost":
            self.client = chromadb.HttpClient(
                host=config["host"], port=config.get("port", 8000)
            )
        else:
            self.client = chromadb.PersistentClient(
                path=config.get("persist_directory", "./data/chroma_db")
            )

        # Get or create collections
        self.entities_collection = self.client.get_or_create_collection(
            name="legal_entities", metadata={"description": "Legal entity embeddings"}
        )

        self.provisions_collection = self.client.get_or_create_collection(
            name="legal_provisions",
            metadata={"description": "Legal provision embeddings"},
        )

    async def upsert_entities(self, entities_data: Dict[str, Dict]) -> bool:
        """Store legal entity embeddings"""
        try:
            ids = list(entities_data.keys())
            documents = []
            metadatas = []

            for entity_id, entity_data in entities_data.items():
                documents.append(entity_data["content"])
                metadatas.append(entity_data["metadata"])

            # Upsert to ChromaDB
            self.entities_collection.upsert(
                ids=ids, documents=documents, metadatas=metadatas
            )
            return True

        except Exception as e:
            print(f"Error upserting entities: {e}")
            return False

    async def query_similar(
        self, query: str, top_k: int = 10, filters: Dict[str, Any] = None
    ) -> List[Dict]:
        """Query similar entities"""
        try:
            # Build where clause for filtering
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        where_clause[key] = value

            # Query ChromaDB
            results = self.entities_collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_clause if where_clause else None,
            )

            # Format results
            formatted_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    result = {
                        "id": results["ids"][0][i],
                        "entity_name": results["metadatas"][0][i].get(
                            "entity_name", ""
                        ),
                        "entity_type": results["metadatas"][0][i].get(
                            "entity_type", ""
                        ),
                        "level": results["metadatas"][0][i].get("level", ""),
                        "distance": (
                            results["distances"][0][i] if results["distances"] else 0.0
                        ),
                        "content": results["documents"][0][i],
                    }
                    formatted_results.append(result)

            return formatted_results

        except Exception as e:
            print(f"Error querying entities: {e}")
            return []

    async def upsert_provisions(self, provisions_data: Dict[str, Dict]) -> bool:
        """Store legal provision embeddings"""
        try:
            ids = list(provisions_data.keys())
            documents = []
            metadatas = []

            for provision_id, provision_data in provisions_data.items():
                documents.append(provision_data["content"])
                metadatas.append(provision_data["metadata"])

            self.provisions_collection.upsert(
                ids=ids, documents=documents, metadatas=metadatas
            )
            return True

        except Exception as e:
            print(f"Error upserting provisions: {e}")
            return False
