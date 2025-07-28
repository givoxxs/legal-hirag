-- Legal Documents Table  
CREATE TABLE legal_documents (  
    id VARCHAR(255) PRIMARY KEY,  
    title TEXT NOT NULL,  
    document_type VARCHAR(100) NOT NULL,  
    source_file VARCHAR(500),  
    structure JSONB NOT NULL,  
    hierarchy_levels TEXT[],  
    total_articles INTEGER DEFAULT 0,  
    total_sections INTEGER DEFAULT 0,  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);  
  
-- Legal Chunks Table (Hierarchical Text Chunks)  
CREATE TABLE legal_chunks (  
    id VARCHAR(255) PRIMARY KEY,  
    document_id VARCHAR(255) REFERENCES legal_documents(id),  
    content TEXT NOT NULL,  
    level VARCHAR(50) NOT NULL, -- 'phan', 'chuong', 'dieu', 'khoan'  
    number VARCHAR(50) NOT NULL,  
    title TEXT,  
    parent_id VARCHAR(255),  
    hierarchy_path TEXT[] NOT NULL,  
    cross_references TEXT[],  
    token_count INTEGER,  
    chunk_order INTEGER,  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);  
  
-- Entity Extraction Logs  
CREATE TABLE extraction_logs (  
    id SERIAL PRIMARY KEY,  
    document_id VARCHAR(255) REFERENCES legal_documents(id),  
    extraction_type VARCHAR(100) NOT NULL,  
    entities_count INTEGER DEFAULT 0,  
    relationships_count INTEGER DEFAULT 0,  
    processing_time_seconds FLOAT,  
    llm_model VARCHAR(100),  
    status VARCHAR(50) DEFAULT 'completed',  
    error_message TEXT,  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);  
  
-- Query Logs  
CREATE TABLE query_logs (  
    id SERIAL PRIMARY KEY,  
    query_text TEXT NOT NULL,  
    query_mode VARCHAR(50) NOT NULL,  
    response_text TEXT,  
    entities_retrieved INTEGER,  
    processing_time_seconds FLOAT,  
    user_feedback INTEGER, -- 1-5 rating  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);  
  
-- Indexes for performance  
CREATE INDEX idx_legal_chunks_document_id ON legal_chunks(document_id);  
CREATE INDEX idx_legal_chunks_level ON legal_chunks(level);  
CREATE INDEX idx_legal_chunks_hierarchy_path ON legal_chunks USING GIN(hierarchy_path);  
CREATE INDEX idx_extraction_logs_document_id ON extraction_logs(document_id);  
CREATE INDEX idx_query_logs_created_at ON query_logs(created_at);