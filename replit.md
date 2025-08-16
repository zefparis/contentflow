# ContentFlow - Automated Content Pipeline

## Overview
ContentFlow is a comprehensive AI-driven content monetization platform designed as a business model where partners publish content through BYOP (Bring Your Own Post) and the platform automatically captures revenue share. The system uses intelligent automation to streamline content creation and distribution across multiple social media platforms while the AI backend manages automated financial distribution and revenue optimization. Partners create and publish content, the platform processes and optimizes it using FFmpeg for platform-specific formats, and the AI orchestrator automatically handles revenue sharing, performance tracking, and financial settlements. The core business model: partners contribute content → AI processes and distributes → revenue is generated → AI automatically allocates financial returns with platform commission.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes (August 16, 2025)
✅ **BYOP Authentication Flow Completely Fixed** (Latest)
- Fixed critical authentication bug preventing BYOP access after email verification
- Corrected redirect flow: email verification now leads directly to BYOP interface
- Added device verification cookie for seamless recognition across sessions
- Strengthened API security: all BYOP endpoints now require proper authentication
- Enhanced magic link system: tokens remain valid for 5 minutes to handle multiple clicks
- Improved client-side cookie detection with robust error handling
- Created comprehensive test suite validating entire authentication flow

✅ **Partner Authentication System Implemented**
- Created complete magic-link authentication for BYOP partners
- Partner profile page with revenue tracking and payment configuration
- Protection of BYOP interface requiring partner login
- Navigation integration with visible "Partenaire" button
- PayPal/Stripe payment method configuration
- API endpoints for partner management and payout requests

✅ **Automated Support System & Risk Detection Implemented**
- Complete SupportBot with intelligent FAQ responses and auto-ticket creation
- RiskBot for click velocity detection and automatic partner flagging
- Database schema with 4 new tables: tickets, ticket_messages, partner_flags, metric_events
- Automated scheduler for support cleanup (6h) and risk sweeps (10min)
- Admin interface for managing held partners and approving large payouts
- Cookie-parser middleware fixed for reliable partner authentication
- Support interface integrated into partner portal with modern responsive design

✅ **AI-Driven Financial Distribution System**
- ContentFlow designed as revenue-sharing platform where partners publish content
- AI backend automatically manages financial distribution and commission allocation
- Platform captures percentage of revenue while partners receive their share
- Automated settlement system with PayPal/Stripe integration for partner payouts
- AI orchestrator optimizes revenue streams and manages financial flows intelligently

## System Architecture
### Frontend Architecture
A React-based Single Page Application (SPA) built with Vite and TypeScript. It utilizes Radix UI components with Tailwind CSS via shadcn/ui for styling, TanStack Query for server state management, and Wouter for client-side routing.

### Backend Architecture
A dual-backend approach combines a Python FastAPI server for content processing and automation with a Node.js Express server for API endpoints and frontend serving.
- **Database Layer**: Drizzle ORM with PostgreSQL (Supabase Database) and SQLAlchemy models for content management.
- **Content Pipeline**: Modular services handle content ingestion (RSS, YouTube CC), asset processing (FFmpeg, quality scoring), AI planning (heuristic-based, A/B testing), compliance checking (risk scoring), multi-platform publishing, scheduling, metrics tracking, and AI-powered performance prediction.
- **AI Orchestrator**: Manages autonomous pipeline operations, revenue optimization, and intelligent action selection.

### Data Storage Solutions
PostgreSQL serves as the primary database, managed with Drizzle ORM. S3-compatible storage is used for processed video assets, and PostgreSQL-backed sessions manage user sessions. SQLite is used for local development.

### Authentication and Authorization
Session-based authentication is implemented with server-side sessions stored in PostgreSQL. JWT support is available for token-based authentication. A basic user schema supports username/password authentication. Magic-link authentication is integrated with Brevo for secure partner portal access.

### Content Processing Pipeline
Supports multi-source ingestion (RSS, YouTube CC, stock content), video transformation using FFmpeg (vertical format conversion, text overlays), AI planning for content optimization (hooks, hashtags, A/B variants), and compliance checking (license validation, content filtering). It features production-ready API integrations for Instagram Reels, TikTok, YouTube Shorts, Reddit, and Pinterest.

### Job Scheduling and Automation
A robust job system orchestrates tasks with priority-based execution. Background tasks enable parallel processing with error handling and retries. An autopilot mode allows fully automated content pipeline operation from ingestion to publication with compliance gates. Thompson Sampling is employed for continuous optimization of content elements.

### AI-Driven Financial Management
The core business model relies on AI-managed revenue distribution where partners publish content via BYOP and the platform automatically captures commission. The AI orchestrator handles financial flows including revenue tracking, commission calculation, partner payouts, and platform profit optimization. Automated settlement processes ensure partners receive their share while the platform maintains its revenue stream.

### UI/UX Decisions
The platform features a clean, modern design leveraging Radix UI and Tailwind CSS, providing a consistent user experience with custom ContentFlow branding. Dashboards provide real-time pipeline metrics and system status.

## External Dependencies
### Core Infrastructure
- **Database**: Supabase PostgreSQL (production) / SQLite (development).
- **File Storage**: AWS S3 support with local fallback.
- **Video Processing**: FFmpeg for video transformation.

### Content Sources
- **RSS Feeds**: Real-time ingestion with filtering.
- **YouTube API**: Closed caption extraction.
- **Stock Content APIs**: Extensible framework for third-party content.
- **SerpAPI Integration**: Google News, YouTube Search, and Google Trends for content discovery and source spawning.

### Social Media Platforms
- **Instagram Graph API**: Official Meta integration for Reels publishing, OAuth, and token management.
- **TikTok API**: Content Posting API.
- **YouTube API**: Shorts publishing.
- **Reddit API**: Subreddit posting.
- **Pinterest API**: Pin creation.

### Other Integrations
- **Brevo Email Marketing**: Automated campaigns, newsletters, and audience nurturing.
- **Supadata AI**: Advanced intelligence layer for performance prediction and content optimization.