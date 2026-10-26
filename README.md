# LeadGen Lite — B2B Lead Finder, Excel Importer, SEO Auditor & Outreach CRM

LeadGen Lite is an enterprise-grade digital marketing lead generation platform. It discovers local businesses using authorized internet data sources, imports and deduplicates existing CSV/Excel datasets, enriches company records, identifies digital marketing opportunities via safe SEO audits, calculates explainable lead scores, generates personalized outreach drafts in English and Hindi, and manages the entire sales lifecycle in a CRM.

---

## 1. Key Features

- **Dual Lead Generation Pipeline**:
  - **Pipeline A (Internet Discovery)**: Pluggable provider adapter architecture supporting official Google Places API, commercial search APIs (SerpApi/ValueSERP), and an offline evaluation business directory. Guarded against fake claims when unconfigured.
  - **Pipeline B (CSV & Excel Processing)**: Multipart upload for `.csv` and `.xlsx` files with automatic column detection, sample preview, duplicate detection, field-safe merging (never overwriting existing non-empty values with blank cells), and downloadable error reports.
- **Company Enrichment**:
  - Tracks individual verification statuses (`Verified`, `Source-listed`, `Inferred`, `Missing`, `Conflicting`).
  - Strict rule: Phone numbers or emails found on public websites are tagged as `Source-listed`, never fabricated or falsely labeled as independently verified.
- **Website SEO Audit Engine**:
  - Deep technical audit analyzing HTTP/HTTPS, page title, meta description, H1 headings, image alt attributes, mobile viewport, robots.txt, sitemap.xml, contact page presence, internal links, and local SEO signals (JSON-LD schema & click-to-call).
  - Robust SSRF protection blocking private RFC1918 networks, loopback (`127.0.0.1`), link-local metadata (`169.254.169.254`), and multicast addresses with strict socket timeouts.
- **Explainable Lead Scoring (0–100)**:
  - 5-factor weighted scoring: Industry fit (25), Website opportunities (25), Business contact quality (15), Specific marketing opportunity (20), Business relevance (15).
  - Priority tiers: High Priority (80–100), Medium Priority (60–79), Low Priority (40–59), Review Required (0–39).
  - Full manual score override support with audit logging.
- **Outreach Message Generation (English & Hindi)**:
  - 5 supported channels: Cold Email, Follow-Up Email, LinkedIn Note (under 300 characters), LinkedIn InMail Draft, WhatsApp Business Draft.
  - Authentic, respectful bilingual drafts in **English** and **Hindi**.
  - 100% free built-in template engine with zero external AI subscriptions, plus optional OpenAI/Gemini LLM adapter.
- **CRM & Follow-Up Tasks**:
  - Complete 12-stage CRM pipeline: `New`, `Research Pending`, `Qualified`, `Ready for Review`, `Contacted`, `Follow-Up`, `Interested`, `Meeting Scheduled`, `Proposal Sent`, `Converted`, `Not Interested`, `Do Not Contact`.
  - Filterable Table View and Kanban Board view.
  - Scheduled follow-up tasks with due dates and overdue alerts.
  - Suppression list management automatically locking opted-out leads to "Do Not Contact".
- **Secure Exports**:
  - Export leads to `.xlsx` (Excel) or `.csv` with filtering.
  - Automatic spreadsheet formula injection sanitization (protecting against `=, +, -, @` exploits).
- **Responsive Blue-and-White UI**:
  - Clean, high-performance interface built with React, TypeScript, Vite, Tailwind CSS, and Lucide Icons.

---

## 2. Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.13 / FastAPI / SQLAlchemy 2.0 / Pydantic v2 / Uvicorn |
| **Frontend** | React 18 / TypeScript / Vite / Tailwind CSS / Lucide React |
| **Database** | SQLite with WAL mode (Local) / PostgreSQL (Render Production) |
| **Data Processing** | Pandas / OpenPyXL / BeautifulSoup4 / HTTPX |
| **Deployment** | GitHub / Render Blueprint (`render.yaml`) / Docker |

---

## 3. Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### Step 1: Clone and Set Up Virtual Environment
```bash
git clone <your-repo-url>
cd CRM

# Create virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 2: Install and Build Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### Step 3: Run the Application
You can run the FastAPI backend which serves both the API and the compiled React SPA:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
Open your browser at:
`http://localhost:8000`

For frontend live-reloading during development:
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173`. Vite will automatically proxy API requests to the FastAPI backend on port 8000.

---

## 4. Running Automated Tests

Run the full pytest suite from the project root:
```bash
.\venv\Scripts\python -m pytest -v
```
All 12 automated tests will execute, verifying:
- Authentication & Multi-tenancy
- Lead CRUD & Deduplication
- CSV/XLSX Upload, Column Mapping & Formula Injection Defense
- SSRF Protection Filters & Web Crawling Safety
- Lead Scoring & Manual Override Audit Logs
- English & Hindi Message Generation
- Follow-up Tasks, Suppression Lists & Dashboard Analytics

---

## 5. Render Deployment Guide (Target Budget: ₹0–₹500/Month)

The project includes a ready-to-use Render Blueprint (`render.yaml`) that provisions:
1. **Web Service**: Free-tier Python environment building frontend assets and running FastAPI.
2. **PostgreSQL Database**: Free-tier managed PostgreSQL instance.

### Step-by-Step Instructions:

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of LeadGen Lite platform"
   git branch -M main
   git remote add origin https://github.com/<your-username>/leadgen-lite.git
   git push -u origin main
   ```

2. **Deploy on Render**:
   - Log in to your [Render Dashboard](https://dashboard.render.com/).
   - Click **New** → **Blueprint**.
   - Connect your GitHub repository.
   - Render will read `render.yaml` and configure:
     - Web service with build command: `npm --prefix frontend install && npm --prefix frontend run build && pip install -r backend/requirements.txt`
     - Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - Health Check endpoint: `/api/health`
     - Managed PostgreSQL database.
   - Click **Apply**. Render will build and deploy the complete platform.

3. **Free Tier & Budget Notes**:
   - **Render Web Service (Free Tier)**: 750 free instance hours per month. Spins down after 15 minutes of inactivity; takes ~30 seconds to wake up on first visit. Cost: **₹0/month**.
   - **Render PostgreSQL (Free Tier)**: 1 GB storage, 97 connection limit. Free for 90 days, then upgradeable or switchable to a persistent hobby plan (~$7 or ~₹580/month) or Supabase free PostgreSQL.
   - **Optional External APIs**:
     - Google Places API: Free tier includes $200 monthly credit (~40,000 requests free).
     - OpenAI/Gemini: Optional; LeadGen Lite runs 100% free with built-in templates out of the box.

---

## 6. Security & Hardening

1. **SSRF Guard**: Custom validator in `app/core/ssrf.py` resolves domain names to IP addresses and rejects all private (RFC1918), loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`), and multicast addresses before establishing any network socket.
2. **CSV Formula Injection Sanitization**: All exported CSV and Excel cells starting with `=`, `+`, `-`, `@`, `\t`, or `\r` are prepended with `'` to prevent DDE code execution in spreadsheet software.
3. **Password Security**: Direct bcrypt hashing with 12 rounds of salt and SHA-256 pre-hashing.
4. **Credential Masking**: All stored API keys in the Settings view are masked (e.g. `AIza...456`) before transmission to the client.

---

## 7. Troubleshooting

- **Database Table Not Found**: Tables are automatically created on startup via `Base.metadata.create_all(bind=engine)`. If migrating manually, delete the local `leadgen_lite.db` or restart the app.
- **Port In Use (8000)**: Start with a custom port: `uvicorn app.main:app --port 8080`.
- **Render Build Timeout**: If frontend building takes longer than usual on free tier, commit the pre-built `frontend/dist` directory to your repository.
