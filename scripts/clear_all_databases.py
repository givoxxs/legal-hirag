#!/usr/bin/env python3
"""
Script để xóa hết dữ liệu trong PostgreSQL, ChromaDB và Neo4j
"""
import asyncio
import asyncpg
from urllib.parse import quote_plus
from neo4j import GraphDatabase
import chromadb
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config


async def clear_postgresql(config):
    """Xóa hết dữ liệu trong PostgreSQL"""
    print("🐘 CLEARING POSTGRESQL DATA...")

    try:
        postgres_config = config["databases"]["postgres"]
        password_encoded = quote_plus(postgres_config["password"])
        # Tạo connection string
        connection_string = (
            f"postgresql://{postgres_config['user']}:{password_encoded}"
            f"@{postgres_config['host']}:{postgres_config['port']}"
            f"/{postgres_config['database']}"
        )

        conn = await asyncpg.connect(connection_string)

        # Xóa dữ liệu theo thứ tự (vì có foreign key constraints)
        print("  🗑️  Deleting extraction_logs...")
        result = await conn.execute("DELETE FROM extraction_logs")
        print(f"     Deleted {result.split()[-1]} rows")

        print("  🗑️  Deleting legal_chunks...")
        result = await conn.execute("DELETE FROM legal_chunks")
        print(f"     Deleted {result.split()[-1]} rows")

        print("  🗑️  Deleting legal_documents...")
        result = await conn.execute("DELETE FROM legal_documents")
        print(f"     Deleted {result.split()[-1]} rows")

        # Reset sequences nếu có
        print("  🔄 Resetting sequences...")
        await conn.execute(
            "ALTER SEQUENCE IF EXISTS extraction_logs_id_seq RESTART WITH 1"
        )

        await conn.close()
        print("✅ PostgreSQL data cleared successfully")
        return True

    except Exception as e:
        print(f"❌ Error clearing PostgreSQL: {e}")
        return False


def clear_neo4j(config):
    """Xóa hết dữ liệu trong Neo4j"""
    print("\n🕸️  CLEARING NEO4J DATA...")

    try:
        neo4j_config = config["databases"]["neo4j"]

        # Tạo driver
        driver = GraphDatabase.driver(
            neo4j_config["uri"], auth=(neo4j_config["user"], neo4j_config["password"])
        )

        with driver.session() as session:
            # Xóa tất cả relationships trước
            print("  🗑️  Deleting all relationships...")
            result = session.run("MATCH ()-[r]->() DELETE r RETURN count(r) as deleted")
            record = result.single()
            print(f"     Deleted {record['deleted']} relationships")

            # Xóa tất cả nodes
            print("  🗑️  Deleting all nodes...")
            result = session.run("MATCH (n) DELETE n RETURN count(n) as deleted")
            record = result.single()
            print(f"     Deleted {record['deleted']} nodes")

            # Verify database is empty
            result = session.run("MATCH (n) RETURN count(n) as count")
            record = result.single()
            if record["count"] == 0:
                print("  ✅ Neo4j database is now empty")
            else:
                print(f"  ⚠️  Warning: {record['count']} nodes still remain")

        driver.close()
        print("✅ Neo4j data cleared successfully")
        return True

    except Exception as e:
        print(f"❌ Error clearing Neo4j: {e}")
        return False


def clear_chromadb(config):
    """Xóa hết dữ liệu trong ChromaDB"""
    print("\n🎨 CLEARING CHROMADB DATA...")

    try:
        chroma_config = config["databases"]["chromadb"]

        # Initialize ChromaDB client
        if "host" in chroma_config and chroma_config.get("host") != "localhost":
            client = chromadb.HttpClient(
                host=chroma_config["host"], port=chroma_config.get("port", 8000)
            )
        else:
            client = chromadb.PersistentClient(
                path=chroma_config.get("persist_directory", "./data/chroma_db")
            )

        # List all collections
        collections = client.list_collections()
        print(f"  Found {len(collections)} collections")

        # Delete each collection
        for collection in collections:
            print(f"  🗑️  Deleting collection: {collection.name}")
            try:
                client.delete_collection(collection.name)
                print(f"     ✅ Deleted collection: {collection.name}")
            except Exception as e:
                print(f"     ❌ Error deleting {collection.name}: {e}")

        # Verify all collections are deleted
        remaining_collections = client.list_collections()
        if len(remaining_collections) == 0:
            print("  ✅ All ChromaDB collections deleted")
        else:
            print(
                f"  ⚠️  Warning: {len(remaining_collections)} collections still remain"
            )
            for col in remaining_collections:
                print(f"     - {col.name}")

        print("✅ ChromaDB data cleared successfully")
        return True

    except Exception as e:
        print(f"❌ Error clearing ChromaDB: {e}")
        return False


async def verify_cleanup(config):
    """Xác minh dữ liệu đã được xóa sạch"""
    print("\n🔍 VERIFYING CLEANUP...")

    # Check PostgreSQL
    try:
        postgres_config = config["databases"]["postgres"]

        password_encoded = quote_plus(postgres_config["password"])
        connection_string = (
            f"postgresql://{postgres_config['user']}:{password_encoded}"
            f"@{postgres_config['host']}:{postgres_config['port']}"
            f"/{postgres_config['database']}"
        )

        conn = await asyncpg.connect(connection_string)

        # Count records in each table
        tables = ["legal_documents", "legal_chunks", "extraction_logs"]
        for table in tables:
            try:
                result = await conn.fetchrow(f"SELECT COUNT(*) as count FROM {table}")
                count = result["count"]
                if count == 0:
                    print(f"  ✅ PostgreSQL {table}: {count} records")
                else:
                    print(f"  ⚠️  PostgreSQL {table}: {count} records remaining")
            except Exception as e:
                print(f"  ❌ Error checking {table}: {e}")

        await conn.close()

    except Exception as e:
        print(f"  ❌ Error verifying PostgreSQL: {e}")

    # Check Neo4j
    try:
        neo4j_config = config["databases"]["neo4j"]
        driver = GraphDatabase.driver(
            neo4j_config["uri"], auth=(neo4j_config["user"], neo4j_config["password"])
        )

        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            record = result.single()
            count = record["count"]
            if count == 0:
                print(f"  ✅ Neo4j nodes: {count}")
            else:
                print(f"  ⚠️  Neo4j nodes: {count} remaining")

            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            record = result.single()
            count = record["count"]
            if count == 0:
                print(f"  ✅ Neo4j relationships: {count}")
            else:
                print(f"  ⚠️  Neo4j relationships: {count} remaining")

        driver.close()

    except Exception as e:
        print(f"  ❌ Error verifying Neo4j: {e}")

    # Check ChromaDB
    try:
        chroma_config = config["databases"]["chromadb"]

        if "host" in chroma_config and chroma_config.get("host") != "localhost":
            client = chromadb.HttpClient(
                host=chroma_config["host"], port=chroma_config.get("port", 8000)
            )
        else:
            client = chromadb.PersistentClient(
                path=chroma_config.get("persist_directory", "./data/chroma_db")
            )

        collections = client.list_collections()
        if len(collections) == 0:
            print(f"  ✅ ChromaDB collections: {len(collections)}")
        else:
            print(f"  ⚠️  ChromaDB collections: {len(collections)} remaining")
            for col in collections:
                count = col.count()
                print(f"     - {col.name}: {count} items")

    except Exception as e:
        print(f"  ❌ Error verifying ChromaDB: {e}")


async def main():
    """Main cleanup function"""
    print("🧹 DATABASE CLEANUP TOOL")
    print("=" * 50)
    print("⚠️  WARNING: This will DELETE ALL DATA in:")
    print("   - PostgreSQL (legal_documents, legal_chunks, extraction_logs)")
    print("   - Neo4j (all nodes and relationships)")
    print("   - ChromaDB (all collections)")
    print()

    # Confirm before proceeding
    response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
    if response not in ["yes", "y"]:
        print("❌ Cleanup cancelled")
        return

    try:
        # Load config
        config = load_config("src/config/legal_config.yaml")
        print("✅ Config loaded successfully")

        # Clear each database
        postgres_success = await clear_postgresql(config)
        neo4j_success = clear_neo4j(config)
        chromadb_success = clear_chromadb(config)

        # Verify cleanup
        await verify_cleanup(config)

        # Summary
        print("\n" + "=" * 50)
        print("🏁 CLEANUP SUMMARY:")
        print(f"   PostgreSQL: {'✅ Success' if postgres_success else '❌ Failed'}")
        print(f"   Neo4j:      {'✅ Success' if neo4j_success else '❌ Failed'}")
        print(f"   ChromaDB:   {'✅ Success' if chromadb_success else '❌ Failed'}")

        if all([postgres_success, neo4j_success, chromadb_success]):
            print("\n🎉 All databases cleared successfully!")
        else:
            print("\n⚠️  Some databases had errors. Please check the logs above.")

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
# python scripts/clear_all_databases.py
