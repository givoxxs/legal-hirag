#!/usr/bin/env python3
"""
Script để kiểm tra kết nối database và setup database nếu cần
"""
import os
import sys
import asyncio
import asyncpg
from pathlib import Path

# Add root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import load_config
from dotenv import load_dotenv

load_dotenv()


async def check_postgres_connection():
    """Kiểm tra kết nối PostgreSQL"""
    print("🔍 KIỂM TRA KẾT NỐI POSTGRESQL...")

    try:
        config = load_config()
        postgres_config = config["databases"]["postgres"]

        print(f"📋 Thông tin kết nối:")
        print(f"  - Host: {postgres_config['host']}")
        print(f"  - Port: {postgres_config['port']}")
        print(f"  - Database: {postgres_config['database']}")
        print(f"  - User: {postgres_config['user']}")

        # Tạo connection string
        connection_string = (
            f"postgresql://{postgres_config['user']}:{postgres_config['password']}"
            f"@{postgres_config['host']}:{postgres_config['port']}"
            f"/{postgres_config['database']}"
        )

        print(f"\n🔌 Đang thử kết nối...")
        conn = await asyncpg.connect(connection_string)

        # Test query
        result = await conn.fetchrow("SELECT version()")
        print(f"✅ Kết nối thành công!")
        print(f"  - PostgreSQL version: {result['version']}")

        await conn.close()
        return True

    except ValueError as e:
        print(f"❌ Lỗi cấu hình: {e}")
        print("💡 Hướng dẫn: Tạo file .env với các environment variables cần thiết")
        return False

    except Exception as e:
        print(f"❌ Không thể kết nối database: {e}")
        print("💡 Hướng dẫn:")
        print("  1. Đảm bảo PostgreSQL server đang chạy")
        print("  2. Kiểm tra thông tin trong file .env")
        print("  3. Tạo database nếu chưa có")
        return False


async def setup_database_tables():
    """Tạo tables nếu chưa có"""
    print("\n🏗️  KIỂM TRA VÀ TẠO TABLES...")

    try:
        config = load_config()
        postgres_config = config["databases"]["postgres"]

        connection_string = (
            f"postgresql://{postgres_config['user']}:{postgres_config['password']}"
            f"@{postgres_config['host']}:{postgres_config['port']}"
            f"/{postgres_config['database']}"
        )

        conn = await asyncpg.connect(connection_string)

        # Kiểm tra table legal_documents
        result = await conn.fetchrow(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'legal_documents'
            );
        """
        )

        if result["exists"]:
            print("✅ Table 'legal_documents' đã tồn tại")
        else:
            print("⚠️  Table 'legal_documents' chưa tồn tại")
            print("💡 Chạy script setup_databases.py để tạo tables")

        # Kiểm tra table legal_chunks
        result = await conn.fetchrow(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'legal_chunks'
            );
        """
        )

        if result["exists"]:
            print("✅ Table 'legal_chunks' đã tồn tại")
        else:
            print("⚠️  Table 'legal_chunks' chưa tồn tại")
            print("💡 Chạy script setup_databases.py để tạo tables")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ Lỗi kiểm tra tables: {e}")
        return False


def check_env_file():
    """Kiểm tra file .env"""
    print("📁 KIỂM TRA FILE .ENV...")

    env_file = Path(".env")
    if not env_file.exists():
        print("❌ File .env không tồn tại!")
        print("💡 Tạo file .env với nội dung:")
        print(
            """
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=legal_hirag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password123

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password

CHROMA_PERSIST_DIRECTORY=./data/chroma_db
OPENAI_API_KEY=your_openai_api_key_here
        """
        )
        return False

    print("✅ File .env tồn tại")

    # Kiểm tra các biến cần thiết
    required_vars = [
        "POSTGRES_HOST",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Thiếu environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ Tất cả environment variables cần thiết đã được set")
        return True


async def main():
    """Main function"""
    print("🚀 KIỂM TRA SETUP DATABASE")
    print("=" * 50)

    # 1. Kiểm tra .env file
    env_ok = check_env_file()
    if not env_ok:
        return

    # 2. Kiểm tra kết nối database
    connection_ok = await check_postgres_connection()
    if not connection_ok:
        return

    # 3. Kiểm tra tables
    await setup_database_tables()

    print("\n" + "=" * 50)
    print("✅ KIỂM TRA HOÀN TẤT!")


if __name__ == "__main__":
    asyncio.run(main())
