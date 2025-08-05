#!/usr/bin/env python3
"""
Script để kiểm tra kết nối Neo4j và setup database nếu cần
"""
import os
import sys
import asyncio
from pathlib import Path
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

# Add root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import load_config
from dotenv import load_dotenv

load_dotenv()


async def check_neo4j_connection():
    """Kiểm tra kết nối Neo4j"""
    print("🔍 KIỂM TRA KẾT NỐI NEO4J...")

    try:
        config = load_config()
        neo4j_config = config["databases"]["neo4j"]

        print(f"📋 Thông tin kết nối:")
        print(f"  - URI: {neo4j_config['uri']}")
        print(f"  - User: {neo4j_config['user']}")
        print(f"  - Password: {neo4j_config['password']}")

        print(f"\n🔌 Đang thử kết nối...")

        # Tạo driver
        driver = AsyncGraphDatabase.driver(
            neo4j_config["uri"], auth=(neo4j_config["user"], neo4j_config["password"])
        )

        # Verify connectivity
        await driver.verify_connectivity()
        print("✅ Kết nối driver thành công!")

        # Test query để lấy thông tin database
        async with driver.session() as session:
            # Kiểm tra version
            result = await session.run(
                "CALL dbms.components() YIELD name, versions, edition"
            )
            components = await result.data()

            if components:
                for component in components:
                    if component["name"] == "Neo4j Kernel":
                        print(f"  - Neo4j version: {component['versions'][0]}")
                        print(f"  - Edition: {component['edition']}")

            # Kiểm tra database hiện tại
            result = await session.run("CALL db.info()")
            db_info = await result.single()
            if db_info:
                print(f"  - Database name: {db_info.get('name', 'N/A')}")

            # Đếm số nodes và relationships
            result = await session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = await result.single()
            print(f"  - Tổng số nodes: {node_count['node_count']}")

            result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = await result.single()
            print(f"  - Tổng số relationships: {rel_count['rel_count']}")

        await driver.close()
        return True

    except AuthError as e:
        print(f"❌ Lỗi xác thực: {e}")
        print("💡 Hướng dẫn:")
        print("  1. Kiểm tra username/password trong file .env")
        print("  2. Đảm bảo user có quyền truy cập database")
        return False

    except ServiceUnavailable as e:
        print(f"❌ Không thể kết nối Neo4j service: {e}")
        print("💡 Hướng dẫn:")
        print("  1. Đảm bảo Neo4j server đang chạy")
        print("  2. Kiểm tra URI trong file .env (bolt://localhost:7687)")
        print("  3. Kiểm tra firewall/port 7687")
        return False

    except ValueError as e:
        print(f"❌ Lỗi cấu hình: {e}")
        print("💡 Hướng dẫn: Tạo file .env với các environment variables cần thiết")
        return False

    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        print("💡 Hướng dẫn:")
        print("  1. Đảm bảo Neo4j server đang chạy")
        print("  2. Kiểm tra thông tin trong file .env")
        print("  3. Thử kết nối bằng Neo4j Browser")
        return False


async def check_neo4j_constraints():
    """Kiểm tra và tạo constraints/indexes cho Neo4j"""
    print("\n🏗️  KIỂM TRA CONSTRAINTS VÀ INDEXES...")

    try:
        config = load_config()
        neo4j_config = config["databases"]["neo4j"]

        driver = AsyncGraphDatabase.driver(
            neo4j_config["uri"], auth=(neo4j_config["user"], neo4j_config["password"])
        )

        async with driver.session() as session:
            # Kiểm tra constraints hiện có
            result = await session.run("SHOW CONSTRAINTS")
            constraints = await result.data()

            print(f"📊 Constraints hiện có: {len(constraints)}")
            for constraint in constraints:
                print(
                    f"  - {constraint.get('name', 'N/A')}: {constraint.get('description', 'N/A')}"
                )

            # Kiểm tra indexes hiện có
            result = await session.run("SHOW INDEXES")
            indexes = await result.data()

            print(f"📊 Indexes hiện có: {len(indexes)}")
            for index in indexes:
                print(
                    f"  - {index.get('name', 'N/A')}: {index.get('labelsOrTypes', 'N/A')} -> {index.get('properties', 'N/A')}"
                )

            # Tạo constraint cho LegalEntity nếu chưa có
            constraint_exists = any(
                "LegalEntity" in str(c.get("description", "")) for c in constraints
            )
            if not constraint_exists:
                print("\n🔧 Tạo constraint cho LegalEntity...")
                try:
                    await session.run(
                        "CREATE CONSTRAINT legal_entity_name IF NOT EXISTS "
                        "FOR (e:LegalEntity) REQUIRE e.name IS UNIQUE"
                    )
                    print("✅ Đã tạo constraint cho LegalEntity.name")
                except Exception as e:
                    print(f"⚠️  Không thể tạo constraint: {e}")
            else:
                print("✅ Constraint cho LegalEntity đã tồn tại")

        await driver.close()
        return True

    except Exception as e:
        print(f"❌ Lỗi kiểm tra constraints: {e}")
        return False


async def test_basic_operations():
    """Test các operations cơ bản"""
    print("\n🧪 TEST CÁC OPERATIONS CƠ BẢN...")

    try:
        config = load_config()
        neo4j_config = config["databases"]["neo4j"]

        driver = AsyncGraphDatabase.driver(
            neo4j_config["uri"], auth=(neo4j_config["user"], neo4j_config["password"])
        )

        async with driver.session() as session:
            # Test tạo node
            print("🔧 Test tạo test node...")
            await session.run(
                """
                MERGE (test:TestNode {name: 'connection_test'})
                SET test.created_at = datetime()
                RETURN test
                """
            )
            print("✅ Tạo test node thành công")

            # Test query node
            print("🔍 Test query test node...")
            result = await session.run(
                "MATCH (test:TestNode {name: 'connection_test'}) RETURN test"
            )
            test_node = await result.single()
            if test_node:
                print("✅ Query test node thành công")
            else:
                print("❌ Không tìm thấy test node")

            # Xóa test node
            print("🗑️  Xóa test node...")
            await session.run(
                "MATCH (test:TestNode {name: 'connection_test'}) DELETE test"
            )
            print("✅ Xóa test node thành công")

        await driver.close()
        return True

    except Exception as e:
        print(f"❌ Lỗi test operations: {e}")
        return False


def check_env_file():
    """Kiểm tra file .env cho Neo4j"""
    print("📁 KIỂM TRA FILE .ENV CHO NEO4J...")

    env_file = Path(".env")
    if not env_file.exists():
        print("❌ File .env không tồn tại!")
        print("💡 Tạo file .env với nội dung:")
        print(
            """
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password

POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=legal_hirag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password123

CHROMA_PERSIST_DIRECTORY=./data/chroma_db
OPENAI_API_KEY=your_openai_api_key_here
        """
        )
        return False

    print("✅ File .env tồn tại")

    # Kiểm tra các biến cần thiết cho Neo4j
    required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Thiếu environment variables cho Neo4j: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ Tất cả environment variables cho Neo4j đã được set")

        # Hiển thị thông tin config
        print(f"  - NEO4J_URI: {os.getenv('NEO4J_URI')}")
        print(f"  - NEO4J_USER: {os.getenv('NEO4J_USER')}")
        print(f"  - NEO4J_PASSWORD: {os.getenv('NEO4J_PASSWORD')}")

        return True


def check_neo4j_installation():
    """Kiểm tra Neo4j có được cài đặt không"""
    print("\n🔍 KIỂM TRA NEO4J INSTALLATION...")

    try:
        import neo4j

        print(f"✅ Neo4j Python driver đã được cài đặt (version: {neo4j.__version__})")
        return True
    except ImportError:
        print("❌ Neo4j Python driver chưa được cài đặt!")
        print("💡 Cài đặt bằng lệnh: pip install neo4j")
        return False


async def main():
    """Main function"""
    print("🚀 KIỂM TRA SETUP NEO4J")
    print("=" * 50)

    # 1. Kiểm tra Neo4j driver
    driver_ok = check_neo4j_installation()
    if not driver_ok:
        return

    # 2. Kiểm tra .env file
    env_ok = check_env_file()
    if not env_ok:
        return

    # 3. Kiểm tra kết nối Neo4j
    connection_ok = await check_neo4j_connection()
    if not connection_ok:
        return

    # 4. Kiểm tra constraints và indexes
    await check_neo4j_constraints()

    # 5. Test basic operations
    await test_basic_operations()

    print("\n" + "=" * 50)
    print("✅ KIỂM TRA NEO4J HOÀN TẤT!")
    print("💡 Neo4j sẵn sàng sử dụng cho Legal HiRAG system!")


if __name__ == "__main__":
    asyncio.run(main())
# python scripts/check_neo4j_connection.py
