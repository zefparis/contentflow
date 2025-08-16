-- ContentFlow Extensions - Add new tables and columns

-- Add new columns to existing tables
ALTER TABLE sources ADD COLUMN keywords VARCHAR(500);
ALTER TABLE sources ADD COLUMN categories VARCHAR(500);
ALTER TABLE sources ADD COLUMN min_duration INTEGER DEFAULT 10;
ALTER TABLE sources ADD COLUMN language VARCHAR(10) DEFAULT 'fr';

ALTER TABLE assets ADD COLUMN phash VARCHAR(64);
ALTER TABLE assets ADD COLUMN keywords VARCHAR(500);

ALTER TABLE posts ADD COLUMN language VARCHAR(10);
ALTER TABLE posts ADD COLUMN hashtags VARCHAR(500);
ALTER TABLE posts ADD COLUMN ab_group VARCHAR(50);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_assets_phash ON assets(phash);
CREATE INDEX IF NOT EXISTS idx_assets_keywords ON assets(keywords);
CREATE INDEX IF NOT EXISTS idx_posts_language ON posts(language);
CREATE INDEX IF NOT EXISTS idx_posts_hashtags ON posts(hashtags);
CREATE INDEX IF NOT EXISTS idx_posts_ab_group ON posts(ab_group);

-- Create new tables
CREATE TABLE IF NOT EXISTS experiments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    variant VARCHAR(50),
    arm_key VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    metrics_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_experiments_arm_key ON experiments(arm_key);

CREATE TABLE IF NOT EXISTS metric_events (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    platform VARCHAR(50),
    kind VARCHAR(20),
    value FLOAT DEFAULT 1.0,
    meta_json TEXT,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_metric_events_platform ON metric_events(platform);
CREATE INDEX IF NOT EXISTS idx_metric_events_kind ON metric_events(kind);
CREATE INDEX IF NOT EXISTS idx_metric_events_ts ON metric_events(ts);

CREATE TABLE IF NOT EXISTS rules (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE,
    value_json TEXT,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rules_key ON rules(key);

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    kind VARCHAR(20) NOT NULL,
    payload_json TEXT,
    status VARCHAR(20) DEFAULT 'queued',
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_jobs_kind ON jobs(kind);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);