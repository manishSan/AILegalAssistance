-- PostgreSQL schema for Legal Case Management
-- Initializes tables and indexes

-- Enable required extensions if available
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Cases table
CREATE TABLE IF NOT EXISTS cases (
    case_id VARCHAR(50) PRIMARY KEY,
    case_type VARCHAR(100) NOT NULL,
    date_filed DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    attorney_id INT,
    case_summary TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Parties table  
CREATE TABLE IF NOT EXISTS parties (
    party_id SERIAL PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL REFERENCES cases(case_id),
    party_type VARCHAR(50) NOT NULL, -- 'plaintiff', 'defendant', 'witness', 'insurance_company'
    name VARCHAR(200) NOT NULL,
    contact_info JSONB,
    insurance_info JSONB
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    doc_id SERIAL PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL REFERENCES cases(case_id),
    file_path VARCHAR(500) NOT NULL,
    doc_category VARCHAR(100) NOT NULL, -- 'medical', 'financial', 'correspondence', 'police_report'
    upload_date DATE NOT NULL,
    document_title VARCHAR(300),
    metadata JSONB
);

-- Case_events table
CREATE TABLE IF NOT EXISTS case_events (
    event_id SERIAL PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL REFERENCES cases(case_id),
    event_date DATE NOT NULL,
    event_type VARCHAR(100) NOT NULL, -- 'accident', 'medical_treatment', 'expense', 'correspondence'
    description TEXT NOT NULL,
    amount NUMERIC(10,2)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_type ON cases(case_type);
CREATE INDEX IF NOT EXISTS idx_parties_case_id ON parties(case_id);
CREATE INDEX IF NOT EXISTS idx_parties_type ON parties(party_type);
CREATE INDEX IF NOT EXISTS idx_documents_case_id ON documents(case_id);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(doc_category);
CREATE INDEX IF NOT EXISTS idx_events_case_id ON case_events(case_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON case_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_date ON case_events(event_date);
