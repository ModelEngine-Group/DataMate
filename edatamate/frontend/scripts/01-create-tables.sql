CREATE TABLE IF NOT EXISTS datasets (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  type VARCHAR(50) NOT NULL,
  category VARCHAR(100),
  size VARCHAR(50),
  item_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(20) DEFAULT 'active',
  tags TEXT[],
  quality DECIMAL(5,2) DEFAULT 0.0,
  annotations_total INTEGER DEFAULT 0,
  annotations_completed INTEGER DEFAULT 0,
  annotations_accuracy DECIMAL(5,2) DEFAULT 0.0,
  lineage_source TEXT,
  lineage_processing TEXT[],
  training_model VARCHAR(100),
  training_accuracy DECIMAL(5,2),
  training_f1_score DECIMAL(5,2)
);

CREATE TABLE IF NOT EXISTS dataset_files (
  id SERIAL PRIMARY KEY,
  dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
  file_name VARCHAR(255) NOT NULL,
  file_path TEXT NOT NULL,
  file_size BIGINT,
  file_type VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS annotations (
  id SERIAL PRIMARY KEY,
  dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
  file_id INTEGER REFERENCES dataset_files(id) ON DELETE CASCADE,
  annotation_data JSONB,
  annotator_id VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(status);
CREATE INDEX IF NOT EXISTS idx_datasets_type ON datasets(type);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON datasets(created_at);
CREATE INDEX IF NOT EXISTS idx_dataset_files_dataset_id ON dataset_files(dataset_id);
CREATE INDEX IF NOT EXISTS idx_annotations_dataset_id ON annotations(dataset_id);
