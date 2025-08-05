import asyncio
import asyncpg
import chromadb
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()


async def setup_postgres():
    """Setup PostgreSQL database"""
    try:
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )

        # Test connection
        result = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL connected: {result}")

        await conn.close()
        return True
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}")
        return False


def setup_neo4j():
    """Setup Neo4j database"""
    try:
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
        )

        with driver.session() as session:
            result = session.run("RETURN 'Neo4j connected' as message")
            print(result.single()["message"])

        driver.close()
        return True
    except Exception as e:
        print(f"Neo4j connection failed: {e}")
        return False


def setup_chromadb():
    """Setup ChromaDB"""
    try:
        persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY")
        os.makedirs(persist_dir, exist_ok=True)

        client = chromadb.PersistentClient(path=persist_dir)

        # Create test collection
        collection = client.get_or_create_collection(
            name="legal_entities_test",
            metadata={"description": "Test collection for legal entities"},
        )

        print("ChromaDB setup successful")
        return True
    except Exception as e:
        print(f"ChromaDB setup failed: {e}")
        return False


async def main():
    """Main setup function"""
    print("Setting up Legal HiRAG databases...")

    # Setup all databases
    postgres_ok = await setup_postgres()
    neo4j_ok = setup_neo4j()
    chroma_ok = setup_chromadb()

    if all([postgres_ok, neo4j_ok, chroma_ok]):
        print("✅ All databases setup successfully!")
    else:
        print("❌ Some databases failed to setup")


if __name__ == "__main__":
    asyncio.run(main())
