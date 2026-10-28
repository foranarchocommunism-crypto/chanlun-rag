-- Derived retrieval projection only. Canonical contracts/schema.sql is unchanged.
PRAGMA foreign_keys=ON;
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE claim_concept(claim_id TEXT NOT NULL,concept_id TEXT NOT NULL,PRIMARY KEY(claim_id,concept_id));
CREATE INDEX claim_concept_concept ON claim_concept(concept_id,claim_id);
CREATE TABLE relation_support(relation_id TEXT NOT NULL,claim_id TEXT NOT NULL,PRIMARY KEY(relation_id,claim_id));
CREATE TABLE evidence_passage(evidence_id TEXT PRIMARY KEY,claim_id TEXT NOT NULL,passage_id TEXT NOT NULL,quote_start INTEGER NOT NULL,quote_end INTEGER NOT NULL);
CREATE INDEX evidence_passage_claim ON evidence_passage(claim_id,evidence_id);
CREATE TABLE retrieval_documents(id TEXT PRIMARY KEY,kind TEXT NOT NULL,review_status TEXT,claim_id TEXT,evidence_id TEXT,passage_id TEXT,document_id TEXT,text TEXT NOT NULL);
CREATE TABLE candidate_triage(candidate_id TEXT PRIMARY KEY,coverage_class TEXT NOT NULL,reviewed_claim_ids TEXT NOT NULL,semantic_status TEXT NOT NULL DEFAULT 'unreviewed');
