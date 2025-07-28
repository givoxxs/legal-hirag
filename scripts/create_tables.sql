-- Legal documents metadata  
CREATE TABLE IF NOT EXISTS legal_documents (  
    id VARCHAR(255) PRIMARY KEY,  
    title TEXT NOT NULL,  
    document_type VARCHAR(100),  
    structure JSONB,  
    created_at TIMESTAMP DEFAULT NOW(),  
    updated_at TIMESTAMP DEFAULT NOW()  
);  
  
-- Legal chunks metadata  
CREATE TABLE IF NOT EXISTS legal_chunks (  
    id VARCHAR(255) PRIMARY KEY,  
    document_id VARCHAR(255) REFERENCES legal_documents(id),  
    content TEXT NOT NULL,  
    level VARCHAR(50),  
    number VARCHAR(50),  
    title TEXT,  
    parent_id VARCHAR(255),  
    hierarchy_path TEXT[],  
    token_count INTEGER,  
    created_at TIMESTAMP DEFAULT NOW()  
);  
  
-- Entity extraction logs  
CREATE TABLE IF NOT EXISTS extraction_logs (  
    id SERIAL PRIMARY KEY,  
    chunk_id VARCHAR(255) REFERENCES legal_chunks(id),  
    entities_count INTEGER,  
    relations_count INTEGER,  
    processing_time INTERVAL,  
    created_at TIMESTAMP DEFAULT NOW()  
);  
  
-- Indexes for performance  
CREATE INDEX IF NOT EXISTS idx_legal_chunks_document_id ON legal_chunks(document_id);  
CREATE INDEX IF NOT EXISTS idx_legal_chunks_level ON legal_chunks(level);  
CREATE INDEX IF NOT EXISTS idx_legal_chunks_parent_id ON legal_chunks(parent_id);