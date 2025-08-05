import asyncpg
import json
from urllib.parse import quote_plus
from typing import Dict, List, Optional, Any
from ..models.legal_schemas import LegalDocument, LegalProvision


class PostgresAdapter:
    """PostgreSQL adapter for legal document metadata"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        password_encoded = quote_plus(config["password"])
        self.connection_string = (
            f"postgresql://{config['user']}:{password_encoded}"
            f"@{config['host']}:{config['port']}"
            f"/{config['database']}"
        )

    async def store_document_metadata(self, document: LegalDocument) -> bool:
        """Store document metadata"""
        try:
            conn = await asyncpg.connect(self.connection_string)

            await conn.execute(
                """  
                INSERT INTO legal_documents (id, title, document_type, structure, created_at)  
                VALUES ($1, $2, $3, $4, NOW())  
                ON CONFLICT (id) DO UPDATE SET  
                    title = $2,  
                    structure = $4,   
                    updated_at = NOW()  
            """,
                document.id,
                document.title,
                document.document_type,
                json.dumps(document.structure),
            )

            await conn.close()
            return True

        except Exception as e:
            print(f"Error storing document metadata: {e}")
            raise e  # Re-raise để storage_manager biết có lỗi

    async def store_provision(self, provision: LegalProvision) -> bool:
        """Store provision metadata"""
        try:
            conn = await asyncpg.connect(self.connection_string)

            await conn.execute(
                """  
                INSERT INTO legal_chunks (  
                    id, document_id, content, level, number, title,   
                    parent_id, hierarchy_path, created_at  
                )  
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())  
                ON CONFLICT (id) DO UPDATE SET  
                    content = $3,  
                    level = $4,  
                    number = $5,  
                    title = $6,  
                    parent_id = $7,  
                    hierarchy_path = $8,  
                    updated_at = NOW()  
            """,
                provision.id,
                provision.document_id,
                provision.content,
                provision.level.value,
                provision.number,
                provision.title,
                provision.parent_id,
                provision.hierarchy_path,
            )

            await conn.close()
            return True

        except Exception as e:
            print(f"Error storing provision: {e}")
            return False

    async def get_document_structure(self, doc_id: str) -> Optional[Dict]:
        """Get document structure"""
        try:
            conn = await asyncpg.connect(self.connection_string)

            result = await conn.fetchrow(
                """  
                SELECT structure FROM legal_documents WHERE id = $1  
            """,
                doc_id,
            )

            await conn.close()

            if result:
                return json.loads(result["structure"])
            return None

        except Exception as e:
            print(f"Error getting document structure: {e}")
            return None

    async def get_provisions_by_document(self, doc_id: str) -> List[Dict]:
        """Get all provisions for a document"""
        try:
            conn = await asyncpg.connect(self.connection_string)
            results = await conn.fetch(
                """  
                SELECT * FROM legal_chunks WHERE document_id = $1  
                ORDER BY hierarchy_path, number  
            """,
                doc_id,
            )

            await conn.close()

            return [dict(row) for row in results]

        except Exception as e:
            print(f"Error getting provisions: {e}")
            return []

    async def get_provisions_by_level(self, doc_id: str, level: str) -> List[Dict]:
        """Get provisions by specific level (phan, chuong, muc, dieu, khoan)"""
        try:
            conn = await asyncpg.connect(self.connection_string)

            results = await conn.fetch(
                """  
                SELECT * FROM legal_chunks   
                WHERE document_id = $1 AND level = $2  
                ORDER BY number  
            """,
                doc_id,
                level,
            )

            await conn.close()

            return [dict(row) for row in results]

        except Exception as e:
            print(f"Error getting provisions by level: {e}")
            return []

    async def close(self):
        """Close PostgreSQL connection"""
        # AsyncPG connections are automatically closed when they go out of scope
        pass
