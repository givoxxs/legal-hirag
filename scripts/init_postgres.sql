-- Legal HiRAG Database Schema  
-- This file contains the complete database schema for the Legal HiRAG system  
  
-- Enable extensions  
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  
  
-- Legal Documents Table  
CREATE TABLE IF NOT EXISTS legal_documents (  
    id VARCHAR(255) PRIMARY KEY,  
    title TEXT NOT NULL,  
    document_type VARCHAR(100) NOT NULL DEFAULT 'legal_code',  
    source_file VARCHAR(500),  
    structure JSONB NOT NULL,  
    hierarchy_levels TEXT[],  
    total_articles INTEGER DEFAULT 0,  
    total_sections INTEGER DEFAULT 0,  
    processing_status VARCHAR(50) DEFAULT 'pending',  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);  
  
-- Legal Chunks Table (Hierarchical Text Chunks)  
CREATE TABLE IF NOT EXISTS legal_chunks (  
    id VARCHAR(255) PRIMARY KEY,  
    document_id VARCHAR(255) REFERENCES legal_documents(id) ON DELETE CASCADE,  
    content TEXT NOT NULL,  
    level VARCHAR(50) NOT NULL CHECK (level IN ('phan', 'chuong', 'muc', 'dieu', 'khoan')), -- Thêm 'muc'  
    number VARCHAR(50) NOT NULL,  
    title TEXT,  
    parent_id VARCHAR(255),  
    hierarchy_path TEXT[] NOT NULL,  
    cross_references TEXT[],  
    token_count INTEGER DEFAULT 0,  
    chunk_order INTEGER DEFAULT 0,  
    embedding_status VARCHAR(50) DEFAULT 'pending',  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);  
  
-- Entity Extraction Logs  
CREATE TABLE IF NOT EXISTS extraction_logs (  
    id SERIAL PRIMARY KEY,  
    document_id VARCHAR(255) REFERENCES legal_documents(id) ON DELETE CASCADE,  
    extraction_type VARCHAR(100) NOT NULL,  
    entities_count INTEGER DEFAULT 0,  
    relationships_count INTEGER DEFAULT 0,  
    processing_time_seconds FLOAT,  
    llm_model VARCHAR(100),  
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),  
    error_message TEXT,  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);  
  
-- Query Logs  
CREATE TABLE IF NOT EXISTS query_logs (  
    id SERIAL PRIMARY KEY,  
    query_text TEXT NOT NULL,  
    query_mode VARCHAR(50) NOT NULL CHECK (query_mode IN ('hierarchical', 'local', 'global', 'bridge', 'provision', 'cross_reference')),  
    response_text TEXT,  
    entities_retrieved INTEGER DEFAULT 0,  
    processing_time_seconds FLOAT,  
    user_feedback INTEGER CHECK (user_feedback >= 1 AND user_feedback <= 5),  
    session_id VARCHAR(255),  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);  
  
-- System Configuration Table  
CREATE TABLE IF NOT EXISTS system_config (  
    key VARCHAR(255) PRIMARY KEY,  
    value JSONB NOT NULL,  
    description TEXT,  
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);  
  
-- Performance Indexes  
CREATE INDEX IF NOT EXISTS idx_legal_chunks_document_id ON legal_chunks(document_id);  
CREATE INDEX IF NOT EXISTS idx_legal_chunks_level ON legal_chunks(level);  
CREATE INDEX IF NOT EXISTS idx_legal_chunks_hierarchy_path ON legal_chunks USING GIN(hierarchy_path);  
CREATE INDEX IF NOT EXISTS idx_legal_chunks_parent_id ON legal_chunks(parent_id);  
CREATE INDEX IF NOT EXISTS idx_extraction_logs_document_id ON extraction_logs(document_id);  
CREATE INDEX IF NOT EXISTS idx_extraction_logs_status ON extraction_logs(status);  
CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);  
CREATE INDEX IF NOT EXISTS idx_query_logs_query_mode ON query_logs(query_mode);  
  
-- Triggers for updated_at timestamps  
CREATE OR REPLACE FUNCTION update_updated_at_column()  
RETURNS TRIGGER AS $$  
BEGIN  
    NEW.updated_at = CURRENT_TIMESTAMP;  
    RETURN NEW;  
END;  
$$ language 'plpgsql';  
  
CREATE TRIGGER update_legal_documents_updated_at   
    BEFORE UPDATE ON legal_documents   
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();  
  
CREATE TRIGGER update_system_config_updated_at   
    BEFORE UPDATE ON system_config   
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();  
  
-- Insert default system configuration  
INSERT INTO system_config (key, value, description) VALUES   
('version', '"1.0.0"', 'Legal HiRAG system version'),  
('default_chunk_size', '1024', 'Default chunk size for text processing'),  
('max_entities_per_chunk', '50', 'Maximum entities to extract per chunk'),  
('hierarchy_levels', '["phan", "chuong", "muc", "dieu", "khoan"]', 'Supported legal hierarchy levels')  
ON CONFLICT (key) DO NOTHING;  
  
-- Comments for documentation  
COMMENT ON TABLE legal_documents IS 'Stores metadata and structure of legal documents';  
COMMENT ON TABLE legal_chunks IS 'Stores hierarchical text chunks from legal documents with support for Mục level';  
COMMENT ON TABLE extraction_logs IS 'Logs entity extraction processes';  
COMMENT ON TABLE query_logs IS 'Logs user queries and system responses';  
COMMENT ON TABLE system_config IS 'System configuration parameters';  
  
-- Additional indexes for Mục level  
CREATE INDEX IF NOT EXISTS idx_legal_chunks_level_muc ON legal_chunks(level) WHERE level = 'muc';