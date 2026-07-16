```
# 📋 Delivery Assurance Copilot

An AI-powered platform that automates the extraction of requirements from documents, generates acceptance criteria and test cases using LLM + RAG, facilitates human-in-the-loop review through an intuitive Streamlit UI, and exports comprehensive traceability matrices. Includes bidirectional Jira integration for seamless workflow synchronization.

## 🎯 Overview

The **Delivery Assurance Copilot** is a production-grade system that:

- **Ingests** BRDs, user stories, API specs, NFRs, SOPs, and QA policy documents (PDF, DOCX, TXT)
- **Extracts** structured requirements using GPT-4o + LangChain ExtractionChain
- **Retrieves** relevant QA standards and policies using RAG with ChromaDB vector store
- **Generates** acceptance criteria, test cases (BDD format), and traceability matrices using LangGraph 6-node workflow
- **Reviews** artifacts through an interactive Streamlit UI with approve/edit/reject capabilities
- **Syncs** bidirectionally with Jira for requirements and test cases management
- **Persists** all data to PostgreSQL with async SQLAlchemy ORM
- **Exports** finalized traceability matrices with coverage analysis as CSV/JSON

**Core Capabilities:**
- ✅ AI-powered requirement extraction from any document type
- ✅ RAG-enhanced generation with source citations
- ✅ Automatic ambiguity detection and gap analysis
- ✅ Human-in-the-loop review and approval workflows
- ✅ Complete traceability from requirements to test cases to source documents
- ✅ Bidirectional Jira integration with webhook support
- ✅ Async processing for high performance
- ✅ Containerized for easy local and cloud deployment

## 📐 Architecture

**End-to-End Data Flow:**

1. **Document Upload** → PDF/DOCX/TXT files uploaded to system
2. **Parsing** → DocumentParser extracts text content
3. **Chunking** → LangChain splits text into 1000-1500 char segments
4. **Embedding** → sentence-transformers generates 384-dim vectors
5. **Vector Storage** → ChromaDB indexes embeddings for semantic search
6. **RAG Retrieval** → Fetches relevant context chunks via similarity search
7. **LLM Chains** → GPT-4o processes with retrieval context
8. **LangGraph Workflow** → 6-node pipeline orchestrates extraction to export:
   - Extract requirements from documents
   - Retrieve relevant standards/policies
   - Generate acceptance criteria with citations
   - Generate test cases in BDD format
   - Analyze coverage gaps
   - Assemble traceability matrix
9. **Persistence** → PostgreSQL stores requirements, tests, criteria, mappings
10. **Human Review** → Streamlit UI for approval/editing/rejection
11. **Export** → Download traceability matrix as CSV/JSON with coverage analysis

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11 |
| **LLM Orchestration** | LangChain + LangGraph |
| **LLM Observability** | LangSmith |
| **LLM Provider** | OpenAI GPT-4o |
| **Vector Store** | ChromaDB (persistent local) |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) |
| **Database** | PostgreSQL 15 |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Database Driver** | asyncpg |
| **Backend API** | FastAPI |
| **Frontend** | Streamlit |
| **Document Parsing** | PyMuPDF, python-docx, pdfplumber |
| **Validation** | Pydantic v2 |
| **Containerization** | Docker + Docker Compose |
| **Secrets** | python-dotenv (.env) |
| **Export** | CSV + JSON |

## 📁 Project Structure

### Root Directory
- `docker-compose.yml` - Docker composition for all services
- `.env.example` - Environment variables template
- `README.md` - Main documentation
- `architecture.md` - Detailed architecture diagrams

### Backend (`backend/`)

**Core Application** (`backend/app/`)
- `main.py` - FastAPI application entry point
- `config.py` - Pydantic settings configuration

**API Routes** (`backend/app/api/`)
- `auth.py` - Authentication endpoints
- `upload.py` - Document upload endpoints
- `extract.py` - Pipeline extraction endpoints
- `review.py` - Review approval endpoints
- `export.py` - CSV/JSON export endpoints

**AI Processing**
- `chains/extraction_chain.py` - LangChain requirement extraction
- `chains/rag_chain.py` - LangChain RAG retrieval & generation
- `graph/state.py` - LangGraph workflow state definition
- `graph/nodes.py` - Workflow node implementations
- `graph/workflow.py` - Compiled LangGraph pipeline

**Data Services** (`backend/app/services/`)
- `parser.py` - Document parser (PDF/DOCX/TXT)
- `chunker.py` - LangChain text splitter
- `embedder.py` - sentence-transformers wrapper
- `chroma_service.py` - ChromaDB vector store

**Database & Models**
- `db/session.py` - Async SQLAlchemy session setup
- `models/db_models.py` - SQLAlchemy ORM models
- `models/pydantic_schemas.py` - Pydantic request/response schemas

**Jira Integration** (`backend/app/addons/jira_addon/`)
- `client.py` - Jira Cloud API wrapper
- `config.py` - Jira configuration models
- `models.py` - Database models for Jira sync
- `schemas.py` - Request/response schemas
- `sync_service.py` - Core sync logic
- `router.py` - Jira API endpoints
- `webhook_service.py` - Webhook handler
- `encryption.py` - Token encryption/decryption
- `tests/` - Unit tests

**Testing** (`backend/tests/`)
- `test_extraction.py` - Extraction pipeline tests
- `test_ingestion.py` - Document ingestion tests
- `test_workflow.py` - LangGraph workflow tests

**Utilities**
- `utils/auth_utils.py` - Authentication utilities
- `requirements.txt` - Python dependencies
- `Dockerfile` - Backend container configuration

### Frontend (`frontend/`)

**Main Application**
- `app.py` - Streamlit main entry point
- `requirements.txt` - Python dependencies
- `Dockerfile` - Frontend container configuration

**Pages** (`frontend/pages/`)
- `0_Login.py` - User authentication page
- `1_Upload.py` - Document upload interface
- `2_Requirements.py` - Requirements view & extraction
- `3_Review.py` - Human-in-the-loop review interface
- `4_Export.py` - Export to CSV/JSON
- `5_Dashboard.py` - Metrics & analytics dashboard
- `6_Jira_Sync.py` - Jira synchronization interface

**Utilities** (`frontend/utils/`)
- `premium_ui.py` - Streamlit UI components

### Support Files

**Scripts** (`scripts/`)
- `create_capstone_project.py` - Project initialization script
- `test_webhook.py` - Webhook testing utility
- `test_webhook_comprehensive.py` - Comprehensive webhook tests

**Sample Data** (`capstone_data/`)
- `docs/` - Sample PDF documents for testing
- `data/` - CSV files with sample data

## 🚀 Getting Started

### Prerequisites

**For Local Deployment:**
- Windows/Mac/Linux operating system
- Docker Desktop installed and running (download from https://www.docker.com/products/docker-desktop)
- Docker Compose (included with Docker Desktop)
- OpenAI API key (get from https://platform.openai.com/api-keys)
- LangSmith API key (optional, for LLM observability at https://smith.langchain.com)

**For Azure Cloud Deployment:**
- Azure account with active subscription
- Azure CLI installed (https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- Docker images built and pushed to Azure Container Registry (ACR)
- Basic understanding of Azure App Service and Azure Database for PostgreSQL

---

## 💻 Local Development - Docker Desktop Setup

### Step 1: Clone Repository & Configure Environment

```bash
# Clone the repository
git clone https://github.com/SumitCodesAI/delivery-assurance-copilot.git
cd delivery-assurance-copilot

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or open with your preferred editor
```

### Step 2: Configure `.env` File

A `.env.example` file is included with all required environment variables. Copy and fill in your credentials:

```bash
cp .env.example .env
```

**Required Environment Variables:**

| Variable | Description | How to Get |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o | https://platform.openai.com/api-keys |
| `LANGCHAIN_API_KEY` | LangSmith API key (optional) | https://smith.langchain.com/ |
| `DATABASE_URL` | PostgreSQL connection string | Auto-configured for Docker |
| `ENCRYPTION_KEY` | Fernet key for Jira token encryption | Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `JIRA_USERNAME` | Jira email (optional) | Your Jira account email |
| `JIRA_API_TOKEN` | Jira API token (optional) | https://id.atlassian.com/manage-profile/security/api-tokens |

See `.env.example` for all available configuration options with descriptions.

**⚠️ IMPORTANT SECURITY NOTES:**
- ✅ **DO NOT** commit `.env` to git (it's in `.gitignore`)
- ✅ **DO NOT** share or expose API keys, tokens, or credentials
- ✅ **DO** rotate API keys regularly in production
- ✅ **DO** use secure credential management (AWS Secrets Manager, Azure KeyVault, etc.) for production

### Step 3: Start Services with Docker Compose

```bash
# Navigate to project root directory
cd delivery-assurance-copilot

# Build and start all services
docker compose up --build

# Or run in background:
docker compose up -d --build
```

This will start:
- **PostgreSQL 15** on `localhost:5432` (database)
- **ChromaDB** on `localhost:8000` (vector store, internal)
- **FastAPI Backend** on `localhost:8000` (REST API)
- **Streamlit Frontend** on `localhost:8501` (web UI)

### Step 4: Access the Application

1. **Streamlit UI**: Open browser → http://localhost:8501
2. **API Documentation**: Open browser → http://localhost:8000/docs (Swagger UI)
3. **API ReDoc**: Open browser → http://localhost:8000/redoc

### Step 5: Verify Setup

```bash
# Check running containers
docker compose ps

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v
```

### Step 6: First Time Usage

1. **Login**: Use any email/password (first user is auto-registered in demo mode)
2. **Create Project**: Name your first project
3. **Upload Documents**: Upload PDF/DOCX/TXT files (requirements documents)
4. **Run Pipeline**: Click "Run Pipeline" to extract requirements
5. **Review**: Approve/edit generated requirements, criteria, and tests
6. **Export**: Download traceability matrix as CSV or JSON
7. **(Optional) Jira Sync**: Configure Jira connection to push/pull data

---

## ☁️ Azure Cloud Deployment

### Architecture Overview

Deployment consists of 3 main services on Azure:

1. **Streamlit Frontend** → Azure App Service
2. **FastAPI Backend** → Azure App Service (with Container Instances)
3. **PostgreSQL 15** → Azure Database for PostgreSQL

### Prerequisites for Azure Deployment

```bash
# Install Azure CLI
# macOS/Linux:
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Windows: Download from https://aka.ms/azure-cli

# Verify installation
az --version

# Login to Azure
az login

# Set your subscription
az account set --subscription "your-subscription-id"
```

### Step 1: Create Azure Resource Group

```bash
# Define variables
RESOURCE_GROUP="delivery-assurance-rg"
LOCATION="eastus"  # Change to your preferred region

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

echo "Resource Group created: $RESOURCE_GROUP"
```

### Step 2: Set Up Azure Container Registry (ACR)

```bash
# Define ACR name (must be lowercase, alphanumeric only)
ACR_NAME="mydeliveryassuranceacr"  # Change this to unique name
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"

# Create Azure Container Registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic

# Enable admin user for login
az acr update \
  --name $ACR_NAME \
  --admin-enabled true

# Get login credentials
az acr credential show \
  --name $ACR_NAME \
  --query "passwords[0].value" \
  --output tsv > acr-password.txt

echo "ACR created: $ACR_LOGIN_SERVER"
echo "Admin username: $ACR_NAME"
echo "Admin password saved to acr-password.txt (do not commit!)"
```

### Step 3: Build & Push Docker Images to ACR

```bash
# Login to ACR
az acr login --name $ACR_NAME

# Build backend image and push
docker build -t ${ACR_LOGIN_SERVER}/backend:latest ./backend
docker push ${ACR_LOGIN_SERVER}/backend:latest

# Build frontend image and push
docker build -t ${ACR_LOGIN_SERVER}/frontend:latest ./frontend
docker push ${ACR_LOGIN_SERVER}/frontend:latest

# Verify images in ACR
az acr repository list --name $ACR_NAME --output table
```

### Step 4: Create Azure Database for PostgreSQL

```bash
# Define database variables
POSTGRES_SERVER_NAME="mydeliverydb"  # Change to unique name
POSTGRES_ADMIN="dbadmin"
POSTGRES_PASSWORD="YourSecurePassword123!"  # Change this securely

# Create PostgreSQL server (Flexible Server)
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $POSTGRES_SERVER_NAME \
  --location $LOCATION \
  --admin-user $POSTGRES_ADMIN \
  --admin-password $POSTGRES_PASSWORD \
  --sku-name Standard_B1s \
  --tier Burstable \
  --storage-size 32 \
  --version 15 \
  --high-availability Disabled \
  --public-access 0.0.0.0

# Create database
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $POSTGRES_SERVER_NAME \
  --database-name delivery_assurance

# Get connection string (save this securely in .env)
POSTGRES_HOST="${POSTGRES_SERVER_NAME}.postgres.database.azure.com"
echo "PostgreSQL Host: $POSTGRES_HOST"
echo "PostgreSQL User: ${POSTGRES_ADMIN}@${POSTGRES_SERVER_NAME}"
echo "Database Name: delivery_assurance"
```

### Step 5: Create App Service Plans

```bash
# Define App Service Plan variables
BACKEND_APP_PLAN="delivery-assurance-backend-plan"
FRONTEND_APP_PLAN="delivery-assurance-frontend-plan"

# Create App Service Plan for Backend
az appservice plan create \
  --name $BACKEND_APP_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

# Create App Service Plan for Frontend
az appservice plan create \
  --name $FRONTEND_APP_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

echo "App Service Plans created"
```

### Step 6: Deploy Backend Service

```bash
# Define backend app name
BACKEND_APP_NAME="delivery-assurance-backend"  # Change to unique name

# Create Web App for Backend
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $BACKEND_APP_PLAN \
  --name $BACKEND_APP_NAME \
  --deployment-container-image-name ${ACR_LOGIN_SERVER}/backend:latest

# Configure container registry access
az webapp config container set \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name ${ACR_LOGIN_SERVER}/backend:latest \
  --docker-registry-server-url https://${ACR_LOGIN_SERVER} \
  --docker-registry-server-user $ACR_NAME \
  --docker-registry-server-password "$(cat acr-password.txt)"

# Set application settings (environment variables)
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME \
  --settings \
    OPENAI_API_KEY="your-openai-api-key" \
    LANGCHAIN_API_KEY="your-langsmith-api-key" \
    LANGCHAIN_TRACING_V2="true" \
    POSTGRES_HOST="${POSTGRES_HOST}" \
    POSTGRES_PORT="5432" \
    POSTGRES_USER="${POSTGRES_ADMIN}@${POSTGRES_SERVER_NAME}" \
    POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    POSTGRES_DB="delivery_assurance" \
    BACKEND_URL="https://${BACKEND_APP_NAME}.azurewebsites.net"

# Start the app
az webapp start --resource-group $RESOURCE_GROUP --name $BACKEND_APP_NAME

echo "Backend deployed: https://${BACKEND_APP_NAME}.azurewebsites.net"
```

### Step 7: Deploy Frontend Service

```bash
# Define frontend app name
FRONTEND_APP_NAME="delivery-assurance-frontend"  # Change to unique name

# Create Web App for Frontend
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $FRONTEND_APP_PLAN \
  --name $FRONTEND_APP_NAME \
  --deployment-container-image-name ${ACR_LOGIN_SERVER}/frontend:latest

# Configure container registry access
az webapp config container set \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name ${ACR_LOGIN_SERVER}/frontend:latest \
  --docker-registry-server-url https://${ACR_LOGIN_SERVER} \
  --docker-registry-server-user $ACR_NAME \
  --docker-registry-server-password "$(cat acr-password.txt)"

# Set application settings
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $FRONTEND_APP_NAME \
  --settings \
    BACKEND_URL="https://${BACKEND_APP_NAME}.azurewebsites.net" \
    STREAMLIT_SERVER_HEADLESS="true"

# Configure Streamlit settings (create startup script)
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $FRONTEND_APP_NAME \
  --startup-file "streamlit run app.py --server.port 8000 --server.address 0.0.0.0"

# Start the app
az webapp start --resource-group $RESOURCE_GROUP --name $FRONTEND_APP_NAME

echo "Frontend deployed: https://${FRONTEND_APP_NAME}.azurewebsites.net"
```

### Step 8: Verify Azure Deployment

```bash
# Check resource group
az group show --name $RESOURCE_GROUP

# List all resources
az resource list --resource-group $RESOURCE_GROUP --output table

# Check web app status
az webapp show --resource-group $RESOURCE_GROUP --name $BACKEND_APP_NAME
az webapp show --resource-group $RESOURCE_GROUP --name $FRONTEND_APP_NAME

# View application logs
az webapp log stream --resource-group $RESOURCE_GROUP --name $BACKEND_APP_NAME
az webapp log stream --resource-group $RESOURCE_GROUP --name $FRONTEND_APP_NAME
```

### Step 9: Access Deployed Application

- **Frontend**: `https://<FRONTEND_APP_NAME>.azurewebsites.net`
- **Backend API**: `https://<BACKEND_APP_NAME>.azurewebsites.net`
- **API Docs**: `https://<BACKEND_APP_NAME>.azurewebsites.net/docs`

### Step 10: Cleanup (Optional)

```bash
# Delete entire resource group (WARNING: deletes all resources)
az group delete --name $RESOURCE_GROUP --yes

# Or delete individual resources:
az webapp delete --resource-group $RESOURCE_GROUP --name $FRONTEND_APP_NAME
az webapp delete --resource-group $RESOURCE_GROUP --name $BACKEND_APP_NAME
az postgres flexible-server delete --resource-group $RESOURCE_GROUP --name $POSTGRES_SERVER_NAME
az acr delete --resource-group $RESOURCE_GROUP --name $ACR_NAME
```

### Azure Deployment Troubleshooting

**Problem**: Container won't start
```bash
# Check logs
az webapp log stream --resource-group $RESOURCE_GROUP --name $BACKEND_APP_NAME

# Restart app
az webapp restart --resource-group $RESOURCE_GROUP --name $BACKEND_APP_NAME
```

**Problem**: Database connection timeout
- Ensure firewall rules allow your client IP
- Check connection string in app settings

**Problem**: Image not found in ACR
- Verify image is pushed: `az acr repository list --name $ACR_NAME`
- Check credentials: `az acr credential show --name $ACR_NAME`

---

## 🔐 Security & Environment Variables

### Environment Variables Required

Create a `.env` file (never commit to git) with:

```env
# API Keys (DO NOT commit to repository)
OPENAI_API_KEY=sk-...
LANGCHAIN_API_KEY=ls-...

# Database (use strong passwords in production)
POSTGRES_PASSWORD=your-secure-password
POSTGRES_USER=copilot_user

# Jira Integration (Optional)
ENCRYPTION_KEY=your-fernet-key

# Application URLs
BACKEND_URL=http://backend:8000
FRONTEND_URL=http://localhost:8501
```

### Security Best Practices

- ✅ Never commit `.env` file to version control
- ✅ Use Azure Key Vault for production secrets (not shown in app settings)
- ✅ Use strong passwords for PostgreSQL (minimum 12 characters)
- ✅ Enable HTTPS for all Azure deployments
- ✅ Use managed identities instead of connection strings where possible
- ✅ Rotate API keys regularly
- ✅ Restrict PostgreSQL firewall rules to specific IP ranges
- ✅ Use environment-specific configuration files

## 🔌 API Endpoints

### Projects
```
POST   /api/v1/projects                          # Create project
GET    /api/v1/projects                          # List projects
GET    /api/v1/projects/{project_id}             # Get project
```

### Upload
```
POST   /api/v1/projects/{project_id}/upload      # Upload document
GET    /api/v1/projects/{project_id}/documents   # List documents
```

### Pipeline
```
POST   /api/v1/projects/{project_id}/run-pipeline    # Run extraction pipeline
GET    /api/v1/projects/{project_id}/requirements    # List requirements
GET    /api/v1/projects/{project_id}/requirements/{req_id}  # Get requirement
```

### Review
```
GET    /api/v1/projects/{project_id}/review         # Get review data
PUT    /api/v1/test-cases/{id}/review              # Update test review
PUT    /api/v1/criteria/{id}/review                # Update criterion review
POST   /api/v1/projects/{project_id}/review-sessions     # Create session
PUT    /api/v1/review-sessions/{id}/complete       # Complete session
```

### Export
```
GET    /api/v1/projects/{project_id}/export/csv      # Export CSV
GET    /api/v1/projects/{project_id}/export/json     # Export JSON
GET    /api/v1/projects/{project_id}/export/summary  # Get summary
```

## 🧪 Running Tests

```bash
# Inside backend container
docker compose exec backend pytest tests/ -v

# Or locally (after pip install -r backend/requirements.txt)
pytest backend/tests/ -v
```

## 📊 Database Schema

### Tables

- **projects**: Projects with status (active/archived)
- **documents**: Uploaded files with chunk counts
- **requirements**: Extracted requirements with priority & ambiguity flags
- **acceptance_criteria**: Generated criteria with source citations
- **test_cases**: Generated test cases with steps
- **traceability_matrices**: Links requirements → tests, coverage status
- **review_sessions**: Tracks reviewer sessions and approval counts

## 🔍 LangSmith Integration

All LLM calls are traced via LangSmith for observability:

1. Set `LANGSMITH_API_KEY` in .env
2. Set `LANGCHAIN_TRACING_V2=true`
3. View traces at: https://smith.langchain.com

## 🌟 Key Features

✅ **Automatic Extraction**: AI-powered requirement extraction from any document
✅ **RAG-Enhanced**: Retrieves relevant standards before generation
✅ **Human-in-the-Loop**: Streamlit UI for review, approval, editing
✅ **Ambiguity Detection**: Flags vague requirements automatically
✅ **Coverage Analysis**: Identifies test gaps and partial coverage
✅ **Traceability**: Links every requirement → test case → source document
✅ **Async & Scalable**: FastAPI + async SQLAlchemy for performance
✅ **LangSmith Observable**: Complete LLM call tracing
✅ **Containerized**: Docker Compose for easy deployment
✅ **Production Ready**: Error handling, validation, persistence

## ⚙️ Configuration

| Env Variable | Default | Description |
|---|---|---|
| OPENAI_API_KEY | - | OpenAI API key (required) |
| LANGCHAIN_API_KEY | - | LangSmith API key (optional) |
| LANGCHAIN_TRACING_V2 | false | Enable LangSmith tracing |
| DATABASE_URL | postgresql+asyncpg://copilot:copilot123@postgres:5432/copilotdb | PostgreSQL URL |
| CHROMA_PERSIST_DIR | /data/chroma | ChromaDB persistence path |
| EMBED_MODEL | all-MiniLM-L6-v2 | sentence-transformers model |
| CHUNK_SIZE | 512 | Document chunk size (tokens) |
| CHUNK_OVERLAP | 50 | Chunk overlap (tokens) |
| TOP_K_RETRIEVAL | 6 | RAG retrieval top-K |

## 🐛 Troubleshooting

### Backend Connection Error
```
❌ Backend Offline
```
- Ensure Docker containers are running: `docker compose ps`
- Check backend logs: `docker compose logs backend`
- Verify API: `curl http://localhost:8000/health`

### Database Connection Error
```
sqlalchemy.exc.OperationalError
```
- Verify PostgreSQL is running: `docker compose ps`
- Check container logs: `docker compose logs postgres`
- Ensure DATABASE_URL is correct in .env

### LLM Rate Limits
```
openai.error.RateLimitError
```
- Add retry logic (already implemented with max_retries=2)
- Reduce TOP_K_RETRIEVAL to lower token usage
- Use GPT-3.5 instead of GPT-4o for testing

### Document Parsing Failures
```
Error parsing PDF
```
- Ensure PDF is not corrupted: try converting to PDF/A
- For DOCX: verify it's valid Microsoft format
- For TXT: ensure UTF-8 encoding

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (Swagger)
- **ReDoc**: http://localhost:8000/redoc
- **Streamlit**: Built-in help in each page

## 🚀 Deployment

### Azure VM

1. SSH into Ubuntu 22.04 VM
2. Install Docker & Docker Compose
3. Clone repo, configure .env
4. Run `docker compose up -d`
5. Access via VM public IP:8501

### Kubernetes

(Future) Create Helm charts for K8s deployment

## 📝 Limitations & Future Work

- [ ] Multi-language support
- [ ] Custom LLM fine-tuning
- [ ] Advanced RAG with hybrid search
- [ ] Real-time collaborative review
- [ ] Integration with Jira/Azure DevOps
- [ ] Test execution tracking
- [ ] Defect linkage

## 📄 License

Proprietary - Sumit's Project

## 👤 Author

Built by an AI-First Development Team

---

## 📐 Detailed Architecture Diagrams

### System Architecture Overview

The complete system is organized into 7 layers with clear separation of concerns:

```mermaid
graph TB
    subgraph User["👤 USER LAYER"]
        U["Streamlit UI<br/>(Port 8501)"]
    end
    
    subgraph Frontend["🎨 FRONTEND - STREAMLIT"]
        P1["📤 Upload Page"]
        P2["📋 Requirements Page"]
        P3["✅ Review Page"]
        P4["📊 Dashboard Page"]
        P5["📥 Export Page"]
        P6["🔗 Jira Sync Page"]
    end
    
    subgraph Backend["🟢 BACKEND API - FASTAPI - Port 8000"]
        A1["Upload Endpoint"]
        A2["Pipeline Endpoint"]
        A3["Review Endpoints"]
        A4["Export Endpoint"]
        A5["Jira Addon Endpoints"]
    end
    
    subgraph Processing["🧠 DATA PROCESSING SERVICES"]
        SV1["DocumentParser<br/>PyMuPDF/python-docx"]
        SV2["TextChunker<br/>1000-1500 chars"]
        SV3["Embedder<br/>all-MiniLM-L6-v2"]
    end
    
    subgraph AI["🤖 AI PROCESSING - LangGraph 6-Node Workflow"]
        LG1["1. Extract Requirements"]
        LG2["2. Retrieve Context<br/>ChromaDB"]
        LG3["3. Generate Acceptance<br/>Criteria"]
        LG4["4. Generate Test Cases"]
        LG5["5. Analyze Coverage Gaps"]
        LG6["6. Assemble Traceability<br/>Matrix"]
    end
    
    subgraph Storage["💾 DATA PERSISTENCE"]
        DB1["ChromaDB<br/>Vector Store"]
        DB2["PostgreSQL 15<br/>Relational Database"]
    end
    
    subgraph Jira["🔗 JIRA INTEGRATION"]
        J1["Jira API Client"]
        J2["Encryption Service"]
    end
    
    U --> Frontend
    Frontend --> Backend
    Backend --> Processing
    Processing --> AI
    AI --> Storage
    Backend --> Jira
    Jira --> J1
    Jira --> J2
    AI --> DB1
    AI --> DB2
```

### Authentication & Login Flow

User authentication uses JWT tokens with session management:

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend
    participant Backend as Backend
    participant Auth as Auth
    participant DB as PostgreSQL
    
    User->>Frontend: Enter credentials
    Frontend->>Backend: POST /auth/login
    Backend->>Auth: Verify credentials
    Auth->>DB: Query user
    DB-->>Auth: User data
    Auth-->>Backend: JWT Token
    Backend-->>Frontend: Return Token
    Frontend->>Frontend: Store in session
    Frontend-->>User: Dashboard
    
    Note over Frontend,Auth: Session Established
```

### Document Upload & Processing Pipeline

The upload pipeline processes documents end-to-end:

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend
    participant Backend as Backend
    participant Parser as Parser
    participant Chunker as Chunker
    participant Embedder as Embedder
    participant ChromaDB as ChromaDB
    participant DB as PostgreSQL
    
    User->>Frontend: Upload PDF/DOCX/TXT
    Frontend->>Backend: POST /upload
    Backend->>Parser: Parse
    Parser-->>Backend: Text
    Backend->>DB: Save doc
    Backend->>Chunker: Chunk text
    Chunker-->>Backend: Chunks
    Backend->>Embedder: Generate vectors
    Embedder-->>Backend: Vectors
    Backend->>ChromaDB: Store vectors
    ChromaDB-->>Backend: Indexed
    Backend-->>Frontend: Success
```

### LangGraph Workflow - 6-Node Pipeline

The core AI processing pipeline executed sequentially:

```mermaid
graph TD
    A["Start Pipeline"] --> B["Initialize Workflow"]
    B --> C["1. Extract Requirements"]
    C --> D["2. Retrieve Context"]
    D --> E["3. Generate Criteria"]
    E --> F["4. Generate Tests"]
    F --> G["5. Analyze Coverage"]
    G --> H["6. Assemble Matrix"]
    H --> I["Persist Results"]
    I --> J["Return Artifacts"]
    
    style C fill:#e1f5ff
    style D fill:#e1f5ff
    style E fill:#e1f5ff
    style F fill:#e1f5ff
    style G fill:#e1f5ff
    style H fill:#e1f5ff
```

### Jira Bidirectional Sync

Real-time synchronization between local requirements and Jira:

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend
    participant Backend as Backend
    participant JiraAddon as JiraAddon
    participant Encryption as Encryption
    participant JiraAPI as JiraAPI
    participant DB as PostgreSQL
    
    User->>Frontend: Configure Jira
    Frontend->>Backend: POST /jira/configure
    Backend->>Encryption: Encrypt Token
    Backend->>DB: Save Config
    
    User->>Frontend: Sync Items
    Frontend->>Backend: POST /jira/sync
    Backend->>JiraAddon: Initiate Sync
    
    JiraAddon->>DB: Fetch Data
    JiraAddon->>Encryption: Decrypt Token
    JiraAddon->>JiraAPI: Create Issues
    JiraAddon->>DB: Save Mappings
```

### API Endpoints Architecture

REST API endpoints organized by category:

```mermaid
graph TB
    Auth["Authentication"]
    Upload["Upload"]
    Pipeline["Pipeline"]
    Review["Review"]
    Export["Export"]
    Jira["Jira"]
    
    Auth --> A1["POST /auth/login"]
    Auth --> A2["POST /auth/logout"]
    Upload --> U1["POST /projects/{id}/upload"]
    Pipeline --> P1["POST /projects/{id}/run-pipeline"]
    Pipeline --> P2["GET /projects/{id}/requirements"]
    Review --> R1["PUT /requirements/{id}"]
    Export --> E1["GET /projects/{id}/export/csv"]
    Export --> E2["GET /projects/{id}/export/json"]
    Jira --> J1["POST /jira/configure"]
    Jira --> J2["POST /jira/sync"]
```

### Database Schema & Relationships

PostgreSQL tables with relationships:

```mermaid
graph LR
    T1["projects"]
    T2["documents"]
    T3["requirements"]
    T4["acceptance_criteria"]
    T5["test_cases"]
    T6["traceability_matrix"]
    T7["review_sessions"]
    J1["jira_connections"]
    J2["jira_issue_mapping"]
    
    T1 --> T2
    T1 --> T3
    T3 --> T4
    T3 --> T5
    T3 --> T6
    T1 --> T7
    T1 --> J1
    J1 --> J2
    
    style T1 fill:#c8e6c9
    style T2 fill:#c8e6c9
    style T3 fill:#c8e6c9
    style T4 fill:#bbdefb
    style T5 fill:#bbdefb
    style T6 fill:#bbdefb
```

### Technology Stack

| Layer | Component | Technology |
|-------|-----------|-----------|
| **Frontend** | UI Framework | Streamlit (Python) |
| **Backend** | API Framework | FastAPI |
| **AI/ML** | LLM Orchestration | LangChain + LangGraph |
| **AI/ML** | LLM Provider | OpenAI GPT-4o |
| **Vector Store** | Embeddings DB | ChromaDB (persistent) |
| **Embeddings** | Model | sentence-transformers (all-MiniLM-L6-v2) |
| **Database** | RDBMS | PostgreSQL 15 |
| **Database** | ORM | SQLAlchemy 2.0 (async) |
| **Database** | Driver | asyncpg |
| **Document Parsing** | PDF/DOCX/TXT | PyMuPDF, python-docx |
| **Validation** | Schema | Pydantic v2 |
| **Integration** | Jira API | requests + encryption |
| **Containerization** | Deployment | Docker + Docker Compose |
| **Observability** | LLM Tracing | LangSmith |

### Data Flow Summary

Complete end-to-end data flow through the system:

1. **User Login** → JWT authentication → Session established
2. **Document Upload** → File parsing → Text chunking → Embedding generation → ChromaDB indexing
3. **Pipeline Execution** → 6-node LangGraph workflow initiated
4. **Requirement Extraction** → GPT-4o extracts from documents
5. **Context Retrieval** → ChromaDB semantic search for relevant chunks
6. **Criteria Generation** → RAGChain creates acceptance criteria with citations
7. **Test Case Generation** → RAGChain creates BDD format tests
8. **Gap Analysis** → Identifies uncovered requirements
9. **Traceability Matrix** → Creates requirement-to-test mappings
10. **Data Persistence** → All results stored in PostgreSQL
11. **User Review** → Streamlit UI for approval/editing
12. **Export** → Download results as CSV/JSON
13. **Jira Sync** (Optional) → Push/pull data from Jira Cloud

---

**Ready to transform your requirements into tests? Start with the Upload page!** 🚀
