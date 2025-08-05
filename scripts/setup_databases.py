#!/usr/bin/env python3
import asyncio
import asyncpg
from neo4j import GraphDatabase
import chromadb
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config


async def setup_postgresql(config):
    """Initialize PostgreSQL database and tables"""
    print("🐘 Setting up PostgreSQL...")

    postgres_config = config["databases"]["postgres"]

    # Connect to PostgreSQL
    conn = await asyncpg.connect(
        host=postgres_config["host"],
        port=postgres_config["port"],
        database=postgres_config["database"],
        user=postgres_config["user"],
        password=postgres_config["password"],
    )

    # Read and execute SQL schema
    schema_file = Path(__file__).parent / "init_postgres.sql"
    with open(schema_file, "r") as f:
        schema_sql = f.read()

    await conn.execute(schema_sql)
    await conn.close()

    print("✅ PostgreSQL setup completed")


def setup_neo4j(config):
    """Initialize Neo4j database with constraints"""
    print("🔗 Setting up Neo4j...")

    neo4j_config = config["databases"]["neo4j"]

    driver = GraphDatabase.driver(
        neo4j_config["uri"], auth=(neo4j_config["user"], neo4j_config["password"])
    )

    with driver.session() as session:
        # Create constraints
        constraints = [
            "CREATE CONSTRAINT legal_entity_name IF NOT EXISTS FOR (e:LegalEntity) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT legal_provision_id IF NOT EXISTS FOR (p:LegalProvision) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT community_id IF NOT EXISTS FOR (c:Community) REQUIRE c.id IS UNIQUE",
        ]

        for constraint in constraints:
            try:
                session.run(constraint)
            except Exception as e:
                print(f"Constraint already exists or error: {e}")

    driver.close()
    print("✅ Neo4j setup completed")


def setup_chromadb(config):
    """Initialize ChromaDB collections"""
    print("🎨 Setting up ChromaDB...")

    chroma_config = config["databases"]["chromadb"]

    # Initialize ChromaDB client
    if "host" in chroma_config:
        client = chromadb.HttpClient(
            host=chroma_config["host"], port=chroma_config["port"]
        )
    else:
        client = chromadb.PersistentClient(path=chroma_config["persist_directory"])

    # Create collections
    collections = [
        {
            "name": "legal_entities",
            "metadata": {
                "description": "Legal entity embeddings for semantic search",
                "embedding_model": "text-embedding-3-large",
            },
        },
        {
            "name": "legal_provisions",
            "metadata": {
                "description": "Legal provision embeddings for hierarchical search",
                "embedding_model": "text-embedding-3-large",
            },
        },
    ]

    for collection_config in collections:
        try:
            client.create_collection(
                name=collection_config["name"], metadata=collection_config["metadata"]
            )
            print(f"   ✅ Created collection: {collection_config['name']}")
        except Exception as e:
            print(
                f"   ⚠️  Collection {collection_config['name']} already exists or error: {e}"
            )

    print("✅ ChromaDB setup completed")


async def main():
    """Main setup function"""
    print("🚀 Setting up Legal HiRAG databases...")

    # Load configuration
    config = load_config("src/config/legal_config.yaml")

    try:
        # Setup databases
        await setup_postgresql(config)
        setup_neo4j(config)
        setup_chromadb(config)

        print("\n🎉 All databases setup completed successfully!")
        print("You can now start processing legal documents.")

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
