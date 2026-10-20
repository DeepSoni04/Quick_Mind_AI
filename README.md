# QueryMind AI — Natural Language Database Assistant

QueryMind AI is an enterprise-grade AI-powered database assistant that translates natural-language queries (English and Hinglish) into dialect-correct, validated SQL for target MySQL and PostgreSQL databases.

---

## Architecture Overview

```
Quick_Mind_AI/
├── frontend/             # React + Vite client application
├── backend/              # FastAPI Python 3.12+ backend
│   ├── app/
│   │   ├── core/         # Security, JWT, symmetric encryption, MongoDB lifecycle
│   │   ├── routers/      # REST API endpoints (auth, queries, databases, sessions, admin, etc.)
│   │   ├── schemas/      # Pydantic v2 validation models
│   │   ├── services/     # SQL AST validator, LLM provider factory, schema discovery, execution
│   │   └── utils/        # Helper functions & formatting utilities
│   ├── tests/            # Pytest test suite (37 unit & integration tests)
│   └── requirements.txt  # Pinned backend dependencies
├── scripts/              # Demo database seeder scripts
├── Dockerfile            # Multi-stage production container
├── docker-compose.yml    # Full-stack local orchestration
├── render.yaml           # Render blueprint specification
└── .github/workflows/    # Automated CI/CD test pipelines
```

---

## Technology Stack

- **Frontend**: React 18, Vite, Vanilla CSS.
- **Backend API**: FastAPI, Uvicorn, Python 3.12+.
- **Internal Database**: MongoDB (via Motor async driver).
- **Target Databases**: MySQL 8+ (`PyMySQL`) and PostgreSQL 14+ (`psycopg2`).
- **SQL Parser & AST Validation**: SQLGlot.
- **Authentication**: JWT with HS256 and Role-Based Access Control (Viewer, Analyst, Admin).
- **LLM Providers**: Configurable (`gemini` via Google Gemini 1.5 Flash, or `mock` for deterministic test suites).

---

## Getting Started Locally

### Prerequisites
- Python 3.12+
- Node.js 18+ & npm
- MongoDB running locally on `mongodb://localhost:27017`

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Run FastAPI backend with Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Health Check: `curl http://localhost:8000/health` → `{"status": "ok"}`
Interactive Swagger Docs: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Running the Automated Test Suite

From the `backend` directory:
```bash
cd backend
pytest -v
```
All 37 test cases run against isolated MongoDB test fixtures and the deterministic mock LLM provider without requiring external API keys.

---

## Deployment Guide

### Render Deployment
This project includes a native `render.yaml` blueprint.
1. Connect your repository to Render.
2. Under **Blueprints**, create a new blueprint instance using `render.yaml`.
3. Provide environment secrets:
   - `MONGODB_URI`: Connection string for MongoDB Atlas.
   - `LLM_API_KEY`: Google Gemini API Key.
   - `ENCRYPTION_KEY`: A 32-byte Fernet key (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`).

### AWS Deployment (ECS / EC2 / App Runner)
A production multi-stage `Dockerfile` is provided.
1. Build and push container to AWS ECR:
   ```bash
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
   docker build -t querymind-backend .
   docker tag querymind-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/querymind-backend:latest
   docker push <account>.dkr.ecr.<region>.amazonaws.com/querymind-backend:latest
   ```
2. Deploy onto AWS App Runner or ECS Fargate, specifying environment variables from `.env.example`.
3. Deploy frontend onto AWS S3 + CloudFront or Amplify.
