# 📖 Installation & Setup Guide

Complete step-by-step guide for setting up the AndroMate AI Agent on your machine.

**Time to Complete:** 15-30 minutes  
**Last Updated:** May 30, 2026

---

## Table of Contents

1. [Prerequisites](#-prerequisites)
2. [Quick Start (5 minutes)](#-quick-start-5-minutes)
3. [Detailed Setup](#-detailed-setup)
4. [Configuration](#-configuration)
5. [Verification](#-verification)
6. [Troubleshooting](#-troubleshooting)

---

## 📋 Prerequisites

### System Requirements

- **Operating System:** Windows, macOS, or Linux
- **Python:** 3.10 or higher
- **RAM:** 4GB minimum (8GB recommended for LLM operations)
- **Disk Space:** 2GB minimum (for Qdrant database)
- **Network:** Internet connection (for OpenAI API or model downloads)

### Software Requirements

**For Local Development (without Docker):**
```bash
# Check Python version
python --version  # Should be 3.10+

# Check pip
pip --version
```

**For Docker Deployment (Recommended):**
```bash
# Check Docker version
docker --version  # Should be 20.10+

# Check Docker Compose
docker-compose --version  # Should be 2.0+
```

### API Keys Required

1. **OpenAI** (if using GPT-4): https://platform.openai.com/api-keys
2. **OpenRouter** (optional): https://openrouter.ai/keys
3. **Local Ollama** (free alternative): https://ollama.ai

---

## ⚡ Quick Start (5 minutes)

### For Docker Users (Fastest)

```bash
# 1. Clone repository
git clone <repo-url>
cd d:\ProjetPfe\AIAgent

# 2. Create .env file
cp .env.example .env

# 3. Edit .env with your API keys
# Open .env and replace:
# - OPENAI_API_KEY=sk-...
# - API_KEY=your-secure-key

# 4. Start all services
docker-compose up -d

# 5. Verify (RAG API has /health endpoint)
curl http://localhost:8001/health
```

### For Local Python Development

```bash
# 1. Clone and navigate
git clone <repo-url>
cd d:\ProjetPfe\AIAgent

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env

# 5. Edit .env with your API keys

# 6. Start Qdrant in Docker
docker run -p 6333:6333 qdrant/qdrant &

# 7. Start Chat API
python -m uvicorn src.api.chat_api:app --reload

# 8. In another terminal, start RAG API
python -m uvicorn src.api.rag_api:app --port 8001 --reload

# 9. Verify (RAG API has /health endpoint)
curl http://localhost:8001/health
```

---

## 🔧 Detailed Setup

### Step 1: Environment Preparation

#### Windows PowerShell

```powershell
# Set execution policy (if needed)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

# Verify Python
python --version

# Navigate to project
cd d:\ProjetPfe\AIAgent
```

#### Linux/Mac

```bash
# Update package manager
sudo apt-get update  # Linux
# or
brew update          # Mac

# Verify Python
python3 --version

# Navigate to project
cd ~/ProjetPfe/AIAgent
```

### Step 2: Create Virtual Environment

#### Windows PowerShell

```powershell
# Create venv
python -m venv venv

# Activate venv
.\venv\Scripts\Activate.ps1

# Verify activation (should show (venv) prefix)
python --version
```

#### Linux/Mac

```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Verify activation
which python  # Should show path to venv
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
pip list | grep qdrant
pip list | grep pydantic
```

**Key Packages Installed:**
- `fastapi==0.135.1` - Web framework
- `uvicorn==0.38.0` - ASGI server
- `qdrant-client==1.17.0` - Vector database
- `pydantic==2.12.5` - Data validation
- `prometheus-client==0.25.0` - Monitoring
- `sentence-transformers==5.3.0` - Embeddings
- `openai==1.35.14` - OpenAI API
- `pytest==9.0.2` - Testing framework
- `python-dotenv` - Environment management

### Step 4: Configuration

#### Create .env File

```bash
# Copy template
cp .env.example .env
```

#### Edit .env (Essential Values)

```env
# 1. Choose LLM Provider
LLM_PROVIDER=openai

# 2. Set API Key
OPENAI_API_KEY=sk-your-actual-key-here
# Get from: https://platform.openai.com/api-keys

# 3. Generate Secure API Key
API_KEY=your-secure-random-key-here
# Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"

# 4. Set Qdrant connection
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

#### Verify Configuration

```bash
# Check .env file
cat .env

# Verify no errors
python -c "from src.config import config; print(f'Config loaded: {config.LLM_PROVIDER}')"
```

### Step 5: Start Services

#### Option A: Docker Compose (Recommended)

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f chat_api
```

#### Option B: Local Development

**Terminal 1 - Qdrant:**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**Terminal 2 - Chat API:**
```bash
python -m uvicorn src.api.chat_api:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 - RAG API:**
```bash
python -m uvicorn src.api.rag_api:app --host 0.0.0.0 --port 8001 --reload
```

### Step 6: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Expected: 69/69 tests passing ✅
```

---

## ⚙️ Configuration Details

### LLM Provider Configuration

#### Option 1: OpenAI (Recommended for Production)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo
```

**Cost:** $0.03/1K tokens (input), $0.06/1K (output)  
**Setup Time:** 5 minutes  
**Recommended for:** Production workloads

#### Option 2: Ollama (Free, Local)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

**Install Ollama:**
```bash
# Download from https://ollama.ai
# Or Docker:
docker run -p 11434:11434 ollama/ollama

# Pull model
ollama pull llama2
```

**Cost:** Free (runs locally)  
**Setup Time:** 10-15 minutes  
**Recommended for:** Development, testing

#### Option 3: OpenRouter (Multiple Models)

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-your-key-here
OPENROUTER_MODEL=openai/gpt-4
```

**Setup:** https://openrouter.ai/keys  
**Cost:** Variable per model  
**Recommended for:** Testing multiple LLMs

### Qdrant Configuration

#### Local Qdrant (Docker)

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Environment variables
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_PREFER_GRPC=true
```

#### Remote Qdrant Server

```bash
# Connect to remote instance
QDRANT_HOST=api.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your-qdrant-key
```

#### Performance Tuning

```env
# Use gRPC for ~20% latency improvement
QDRANT_PREFER_GRPC=true

# Increase timeout for slower connections
QDRANT_TIMEOUT=30

# Connection pool size
QDRANT_POOL_SIZE=10
```

### Performance Configuration

```env
# Timeouts
LLM_TIMEOUT_SECONDS=120        # Give LLM time to respond
MIDDLEWARE_TIMEOUT_SECONDS=120 # HTTP middleware timeout

# Caching
CACHE_TTL_SECONDS=3600         # Cache for 1 hour
CACHE_MAX_SIZE=1000            # Store up to 1000 responses

# Memory Management
CLEANUP_INTERVAL_SECONDS=300   # Run cleanup every 5 min
CLEANUP_MAX_AGE_HOURS=1        # Remove old entries after 1 hour
```

---

## ✅ Verification

### 1. Check Installation

```bash
# Verify Python packages
pip list

# Check key packages
python -c "import fastapi; import qdrant_client; import pydantic; print('✅ All packages installed')"
```

### 2. Test API Connectivity

```bash
# Health check (RAG API only - Chat API doesn't have /health endpoint)
curl -X GET http://localhost:8001/health

# Expected response:
# {"message": "RAG API running", "qdrant_connected": true}
```

### 3. Test with Authentication

```bash
# Get your API key from .env
API_KEY=$(grep "^API_KEY=" .env | cut -d'=' -f2)

# Test authenticated request (RAG API)
curl -X GET http://localhost:8001/health \
  -H "Authorization: Bearer $API_KEY"
```

### 4. Run Unit Tests

```bash
# Run all tests
pytest tests/ -v --tb=short

# Expected output:
# tests/test_*.py PASSED [100%]
# ============ 69 passed in 12.34s ============
```

### 5. Test Chat Endpoint

```bash
# Get API key
API_KEY=$(grep "^API_KEY=" .env | cut -d'=' -f2)

# Send test request
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Send a message on WhatsApp",
    "type_intent": "workflow_generation"
  }'

# Expected: 200 OK with workflow JSON
```

### 6. Monitor Performance

```bash
# Check metrics
curl http://localhost:8000/metrics | head -20

# Expected: Prometheus metrics output
```

---

## 🐛 Troubleshooting

### Issue 1: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
# Verify virtual environment is activated
which python  # Should show path to venv

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 2: "Cannot connect to Qdrant at localhost:6333"

**Solution:**
```bash
# Check Qdrant is running
docker ps | grep qdrant

# If not running, start it
docker run -p 6333:6333 qdrant/qdrant &

# Check connectivity
curl http://localhost:6333/health
```

### Issue 3: "OpenAI API key not found"

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Verify API key is set
grep "OPENAI_API_KEY" .env

# Get key from OpenAI dashboard
# https://platform.openai.com/api-keys
```

### Issue 4: "Port 8000 already in use"

**Solution:**
```bash
# Kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8000
kill -9 <PID>

# Or use different port
python -m uvicorn src.api.chat_api:app --port 8001
```

### Issue 5: "Out of memory / Memory leak"

**Solution:**
```bash
# Check memory cleanup is running
tail -f logs/app.log | grep "MEMORY"

# Increase cleanup frequency
CLEANUP_INTERVAL_SECONDS=180  # Every 3 minutes

# Restart the application
docker-compose restart chat_api
# or
kill the Python process and restart
```

### Issue 6: "Tests failing"

**Solution:**
```bash
# Run tests with verbose output
pytest tests/ -vv --tb=long

# Check for import errors
python -m pytest --collect-only

# Run specific test
pytest tests/test_chat_complete_pipeline.py::test_generation -v
```

---

## 📞 Getting Help

### Check Documentation

1. **General:** [README.md](README.md)
2. **API Usage:** [API.md](API.md)
3. **System Design:** [ARCHITECTURE.md](ARCHITECTURE.md)

### Review Logs

```bash
# View real-time logs
tail -f logs/app.log

# Search for errors
grep "ERROR" logs/app.log

# Check specific module
grep "\[CHAT\]" logs/app.log
```

### Debug Commands

```bash
# Check configuration
python -c "from src.config import config; print(config.__dict__)"

# Verify imports
python -c "from src.api.chat_api import app; print('✅ Chat API imports OK')"

# Test Qdrant connection
python -c "from src.clients import get_qdrant_client; c = get_qdrant_client(); print('✅ Qdrant connected')"

# Test LLM provider
python -c "from src.clients import get_llm_client; c = get_llm_client(); print('✅ LLM provider ready')"
```

---

## ✨ Next Steps

After successful installation:

1. **Read API Documentation:** [API.md](API.md)
2. **Understand Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Configure Monitoring:** Set up Grafana dashboard
4. **Run Integration Tests:** Test end-to-end workflows
5. **Deploy to Production:** Follow Docker deployment guide

---

## 📊 System Check Script

Save as `check_system.py`:

```python
#!/usr/bin/env python
import sys
import subprocess

def check(name, command):
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {name}")
            return True
        else:
            print(f"❌ {name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False

print("🔍 System Check\n")
checks = [
    ("Python 3.10+", "python --version"),
    ("pip", "pip --version"),
    ("Docker", "docker --version"),
    ("Docker Compose", "docker-compose --version"),
]

passed = sum(check(name, cmd) for name, cmd in checks)
print(f"\n✅ Passed: {passed}/{len(checks)}")
sys.exit(0 if passed == len(checks) else 1)
```

Run with:
```bash
python check_system.py
```

---

**Ready to start?** Jump to [Quick Start](#-quick-start-5-minutes) or check [README.md](README.md)!
