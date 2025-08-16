-- Migration pour AI Orchestrator
-- Tables pour l'état et les actions de l'agent autonome

CREATE TABLE IF NOT EXISTS agent_state (
  id TEXT PRIMARY KEY,
  key TEXT UNIQUE,
  value_json TEXT NOT NULL DEFAULT '{}',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_actions (
  id TEXT PRIMARY KEY,
  tick_ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  kind TEXT,
  target TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  decision_score REAL NOT NULL DEFAULT 0.0,
  executed BOOLEAN NOT NULL DEFAULT FALSE,
  success BOOLEAN NOT NULL DEFAULT FALSE,
  error TEXT
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_agent_actions_tick ON agent_actions(tick_ts);
CREATE INDEX IF NOT EXISTS idx_agent_actions_kind ON agent_actions(kind);
CREATE INDEX IF NOT EXISTS idx_agent_state_key ON agent_state(key);

-- Règles par défaut pour l'AI Orchestrator
INSERT INTO rules (key, value, description) VALUES 
(
  'ai_orchestrator_config',
  '{"enabled": true, "tick_interval": 10, "max_actions_per_tick": 5}',
  'Configuration globale AI Orchestrator'
)
ON CONFLICT (key) DO NOTHING;

INSERT INTO rules (key, value, description) VALUES 
(
  'scheduler_windows',
  '{"youtube": ["09:00-12:00", "14:00-17:00", "19:00-22:00"], "instagram": ["12:00-14:00", "18:00-21:00"], "reddit": ["10:00-16:00", "20:00-23:00"]}',
  'Fenêtres optimales de publication par plateforme'
)
ON CONFLICT (key) DO NOTHING;

INSERT INTO rules (key, value, description) VALUES 
(
  'rate_limits',
  '{"youtube": {"per_hour": 10, "per_day": 100}, "instagram": {"per_hour": 5, "per_day": 50}, "reddit": {"per_hour": 3, "per_day": 30}}',
  'Rate limits par plateforme'
)
ON CONFLICT (key) DO NOTHING;