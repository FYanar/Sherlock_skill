"""
Database schema definitions for OneClickDock Knowledge Base.
Implements Cerebras single-table embeddings + FTS + metadata design.
"""

CREATE_EMBEDDINGS_TABLE = """
CREATE TABLE IF NOT EXISTS knowledge_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL DEFAULT 'OneClickDock',
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    chunk_type TEXT NOT NULL,
    parent_id TEXT DEFAULT '',
    start_line INTEGER DEFAULT 0,
    end_line INTEGER DEFAULT 0,
    raw_content TEXT NOT NULL,
    distilled_summary TEXT DEFAULT '',
    metadata_json TEXT DEFAULT '{}',
    embedding_blob BLOB,
    content_hash TEXT NOT NULL,
    idf_score REAL DEFAULT 1.0,
    created_at REAL NOT NULL
);
"""

CREATE_FTS_TABLE = """
CREATE VIRTUAL TABLE IF NOT EXISTS fts_embeddings USING fts5(
    source_id,
    chunk_type,
    raw_content,
    distilled_summary,
    metadata_json,
    content='knowledge_embeddings',
    content_rowid='id'
);
"""

CREATE_FTS_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS knowledge_embeddings_ai AFTER INSERT ON knowledge_embeddings BEGIN
  INSERT INTO fts_embeddings(rowid, source_id, chunk_type, raw_content, distilled_summary, metadata_json)
  VALUES (new.id, new.source_id, new.chunk_type, new.raw_content, new.distilled_summary, new.metadata_json);
END;

CREATE TRIGGER IF NOT EXISTS knowledge_embeddings_ad AFTER DELETE ON knowledge_embeddings BEGIN
  INSERT INTO fts_embeddings(fts_embeddings, rowid, source_id, chunk_type, raw_content, distilled_summary, metadata_json)
  VALUES('delete', old.id, old.source_id, old.chunk_type, old.raw_content, old.distilled_summary, old.metadata_json);
END;

CREATE TRIGGER IF NOT EXISTS knowledge_embeddings_au AFTER UPDATE ON knowledge_embeddings BEGIN
  INSERT INTO fts_embeddings(fts_embeddings, rowid, source_id, chunk_type, raw_content, distilled_summary, metadata_json)
  VALUES('delete', old.id, old.source_id, old.chunk_type, old.raw_content, old.distilled_summary, old.metadata_json);
  INSERT INTO fts_embeddings(rowid, source_id, chunk_type, raw_content, distilled_summary, metadata_json)
  VALUES (new.id, new.source_id, new.chunk_type, new.raw_content, new.distilled_summary, new.metadata_json);
END;
"""

CREATE_SYNC_METADATA_TABLE = """
CREATE TABLE IF NOT EXISTS sync_metadata (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    chunk_count INTEGER NOT NULL,
    last_synced REAL NOT NULL
);
"""

CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON knowledge_embeddings(source_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_project ON knowledge_embeddings(project);
CREATE INDEX IF NOT EXISTS idx_embeddings_type ON knowledge_embeddings(source_type, chunk_type);
"""
