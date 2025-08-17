-- Création de la table 'jobs' si elle n'existe pas
CREATE TABLE IF NOT EXISTS public.jobs (
    id SERIAL PRIMARY KEY,
    idempotency_key VARCHAR(32) UNIQUE,
    payload JSONB,
    status VARCHAR(50) DEFAULT 'queued',
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result TEXT,
    error TEXT
);

-- Création de la table 'runs' si elle n'existe pas
CREATE TABLE IF NOT EXISTS public.runs (
    id SERIAL PRIMARY KEY,
    status VARCHAR(20) DEFAULT 'pending',
    kind VARCHAR(50),
    details TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Création des index pour la table 'runs'
CREATE INDEX IF NOT EXISTS idx_runs_status ON public.runs (status);
CREATE INDEX IF NOT EXISTS idx_runs_kind ON public.runs (kind);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON public.runs (created_at);

-- Création de l'index pour la colonne idempotency_key de la table 'jobs' s'il n'existe pas
CREATE INDEX IF NOT EXISTS idx_jobs_idempotency_key ON public.jobs (idempotency_key);

-- Commentaires pour la table 'runs'
COMMENT ON TABLE public.runs IS 'Tracks execution runs of various jobs';
COMMENT ON COLUMN public.runs.status IS 'pending, running, completed, failed';
COMMENT ON COLUMN public.runs.kind IS 'Type of run (import, export, publish, etc.)';
COMMENT ON COLUMN public.runs.details IS 'JSON details about the run';

-- Vérification des tables créées
SELECT 'jobs' AS table_name, 
       (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'jobs') AS exists,
       (SELECT COUNT(*) FROM jobs) AS row_count
UNION ALL
SELECT 'runs' AS table_name,
       (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'runs') AS exists,
       (SELECT COUNT(*) FROM runs) AS row_count;
