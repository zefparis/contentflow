Config Replit + deps

Fichiers:

.replit
replit.nix
requirements.txt
.env.example
README.md
Makefile


Contenu attendu (compact) :

.replit ⇒ run = "bash -lc 'export PYTHONUNBUFFERED=1 && pip install -r requirements.txt && make build-css || true && python -m app.main'"

replit.nix ⇒ pkgs: python311, pip, ffmpeg, nodejs_20

requirements.txt (versions fixes, courtes):
fastapi==0.115.0 uvicorn[standard]==0.30.6 jinja2==3.1.4 python-multipart==0.0.9 pydantic==2.8.2 sqlalchemy==2.0.32 psycopg[binary]==3.2.1 httpx==0.27.0 boto3==1.34.162 apscheduler==3.10.4 python-dotenv==1.0.1 orjson==3.10.7

.env.example (placeholders): DATABASE_URL=sqlite:///./local.db (par défaut), + S3_, AFFIL_, APP_BASE_URL, JWT_SECRET

Makefile: cibles dev, seed, build-css

README.md: quickstart 10 lignes (copier .env, run, où cliquer)

2) Arbo + modules

Crée l’arbo suivante et implémente le minimum fonctionnel :

app/
  main.py
  config.py
  db.py
  models.py
  schemas.py
  deps.py
  utils/{logger.py,s3.py,ffmpeg.py,bandit.py,metrics.py}
  services/{sources.py,assets.py,posts.py,publish.py,ai_planner.py,compliance.py,scheduler.py}
  routes/{__init__.py,health.py,ui.py,sources.py,assets.py,posts.py,jobs.py,reports.py}
  workers/autopilot.py
  templates/{base.html,dashboard.html,assets.html,composer.html,scheduler.html,runs.html,reports.html}
  static/css/{tailwind.css,out.css}
infra/seed.py

Contraintes d’implémentation (brefs):

FastAPI: monte routes; Jinja2Templates pour pages; statiques static/.

DB: SQLAlchemy + SQLite par défaut (pour boot Replit). Si DATABASE_URL Postgres fourni, utilise-le.

Modèles:

Source(id, kind[rss|youtube_cc|stock], url, enabled, created_at)

Asset(id, source_id, status[new|ready|failed], meta_json, s3_key, duration, lang)

Post(id, asset_id, platform, title, description, shortlink, status[queued|posted|failed], metrics_json, created_at)

Run(id, kind[ingest|transform|publish], status, logs, created_at)

Link(id, affiliate_url, utm, platform_hint)

Pages UI (HTMX+Tailwind):

/ (dashboard KPIs: #assets new/ready, #posts queued/posted)

/assets (liste + bouton “Transform”)

/composer (éditer titre/desc/cta d’un Post brouillon + “Queue publish”)

/scheduler (boutons Run Now: ingest/transform/publish)

/runs (liste exécutions + logs)

/reports (simulateur: vues, ctr, epc ⇒ €)

APScheduler (in-process) avec 3 jobs:

job_ingest() toutes 30 min (RSS mock + YouTube CC mock: créer 2 Assets de démo si pas d’API)

job_transform() toutes 30 min (FFmpeg sur un clip de démo local, 3s → MP4; sinon générer un mp4 test noir avec color=c=black:s=1080x1920:d=3; upload S3 si S3_* set, sinon local)

job_publish() toutes 20 min (stub: marque Post→posted et log)

S3: utils/s3.py gère no-op si env S3_* absent (retourne URL locale).

FFmpeg: utils/ffmpeg.py expose make_shorts(input_url_or_path, plan) -> output_path

scale 1080x1920, 30fps, overlay drawtext hook + attribution (texte fixe si plan vide).

AI planner: services/ai_planner.py fournit generate_plan_heuristic(asset) (segments ≤30s, hook texte, attribution depuis meta). LLM non requis MVP (préparer stub generate_plan_llm mais ne pas appeler).

Compliance: services/compliance.py calcule risk_score (0..1). Si plan sans attribution ⇒ risk ≥ 0.5.

Bandit: utils/bandit.py Thompson sampling minimal sur bras {platform,lang,hook_id} en mémoire (ou via metrics_json).

Publish stubs: services/publish.py fournit publish(platform, post) ⇒ pour MVP, change status en posted + timestamp + log (pas d’API externe).

Autopilot: workers/autopilot.py autopilot_tick() = enchaîne: select Assets new → plan → ffmpeg → Asset ready + Post queued → queue publish (respect risk gate: risk<0.2).

3) Routes essentielles (implémenter simples)

GET /healthz → {ok:true}

UI:

GET / → dashboard.html (KPI from DB counts)

GET /assets → table Assets + bouton POST /assets/{id}/transform

POST /assets/{id}/transform → lance transform sync (petite vidéo test), crée/MAJ Post brouillon

GET /composer → sélection Post (dropdown) + form titre/desc/cta + POST /posts/{id}/queue

POST /posts/{id}/queue → mark queued

GET /scheduler → 3 boutons “Run Now” (POST /jobs/ingest, /jobs/transform, /jobs/publish)

GET /runs → liste derniers Run (kind, status, logs court)

GET /reports → form HTMX (vues, ctr%, epc€) ⇒ renvoie € calculé (server-side)

API jobs:

POST /jobs/ingest → exécute job_ingest() immédiat + log un Run

POST /jobs/transform → idem job_transform()

POST /jobs/publish → idem job_publish()

4) Démarrage clean (acceptance)

Lancer et ouvrir / sans erreur

/healthz = 200

/jobs/ingest crée ≥1 Asset.new

/jobs/transform produit un MP4 de démo et crée Asset.ready + Post.queued

/jobs/publish met Post.status=posted

/reports calcule € = vues * (ctr/100) * epc

Pas de crash si S3 ou Postgres absents (fallback SQLite + no-op S3)

5) Seed minimal

infra/seed.py : insérer 1 Source(rss, url="https://example.com/feed"), 1 Link(affiliate_url="https://ex.com", utm="utm_source={platform}")

6) Sécurité/ToS rapide

Pas de scraping illégal; contenu démo local

Attribution visible dans vidéo démo

Champ description doit inclure #ad si shortlink présent

Génère maintenant tous les fichiers ci-dessus avec code complet compact.
Objectif: que ça boot sur Replit tel quel et exécute un cycle : Ingest → Transform (MP4 test) → Queue → Publish (stub) → visible dans UI.