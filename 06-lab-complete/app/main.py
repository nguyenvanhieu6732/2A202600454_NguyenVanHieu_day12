"""
Production AI Agent — Final Version (Part 6)
Kết hợp tất cả các Day 12 concepts với kiến trúc Stateless thực thụ.

Checklist:
  ✅ Config từ environment (12-Factor)
  ✅ Structured JSON logging
  ✅ Stateless design (Redis-backed everything)
  ✅ Modular structure (auth, rate_limiter, cost_guard)
  ✅ Conversation History trong Redis
  ✅ Health check + Readiness probe
  ✅ Graceful shutdown
"""
import time
import logging
import json
import uuid
from datetime import datetime, timezone
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Security, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Core components
from app.config import settings
from app.storage import storage
from app.auth import verify_api_key
from app.rate_limiter import check_rate_limit
from app.cost_guard import check_and_record_cost

# Mock LLM
from utils.mock_llm import ask as llm_ask

# ─────────────────────────────────────────────────────────
# Logging — JSON structured
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False

# ─────────────────────────────────────────────────────────
# Conversation History Helpers (Redis-backed)
# ─────────────────────────────────────────────────────────
def load_history(session_id: str) -> list:
    r = storage.get_redis()
    if not r: return []
    data = r.get(f"history:{session_id}")
    return json.loads(data) if data else []

def save_history(session_id: str, history: list, ttl: int = 3600):
    r = storage.get_redis()
    if not r: return
    # Max history length: 10 messages
    if len(history) > 10:
        history = history[-10:]
    r.setex(f"history:{session_id}", ttl, json.dumps(history))

# ─────────────────────────────────────────────────────────
# Graceful Shutdown Handler
# ─────────────────────────────────────────────────────────
def handle_sigterm(signum, frame):
    logger.info(json.dumps({"event": "signal", "signum": "SIGTERM"}))
    # Note: Uvicorn/FastAPI handles the actual shutdown via lifespan

signal.signal(signal.SIGTERM, handle_sigterm)

# ─────────────────────────────────────────────────────────
# Lifespan (Startup/Shutdown)
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "environment": settings.environment,
        "storage": "Redis ✅" if storage.use_redis else "In-memory ⚠️"
    }))
    
    # Simulate some init time
    time.sleep(0.5)
    _is_ready = True
    
    yield
    
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))

# ─────────────────────────────────────────────────────────
# API Configuration
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(None, description="Conversation session ID")

class AskResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    history_count: int
    model: str
    timestamp: str

# ─────────────────────────────────────────────────────────
# Middleware for Request Logging & Security Headers
# ─────────────────────────────────────────────────────────
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    start = time.time()
    response: Response = await call_next(request)
    
    # Modern security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if "server" in response.headers:
        del response.headers["server"]
    
    duration = round((time.time() - start) * 1000, 1)
    logger.info(json.dumps({
        "event": "request",
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "ms": duration,
        "client": str(request.client.host) if request.client else "unknown"
    }))
    return response

# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────
@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "status": "operational",
        "environment": settings.environment,
        "redis_connected": storage.use_redis
    }

@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    _key: str = Depends(verify_api_key),
):
    """
    Phần lõi của Part 6:
    1. Xác thực (API Key)
    2. Rate limit (Redis)
    3. Kiểm tra budget (Redis)
    4. Load conversation history (Redis)
    5. Gọi LLM
    6. Lưu history mới (Redis)
    """
    # 1. Rate Limit check
    check_rate_limit(_key[:8]) # Bucket by API key prefix
    
    # 2. Daily budget check (pre-call)
    input_tokens = len(body.question.split()) * 2
    check_and_record_cost(input_tokens, 0)

    # 3. Conversation History
    session_id = body.session_id or str(uuid.uuid4())
    history = load_history(session_id)
    
    # Add user message to history
    history.append({"role": "user", "content": body.question})

    # 4. Agent logic (LLM Call)
    # Note: Mock LLM doesn't use history yet, but we're architected for it
    answer = llm_ask(body.question)
    
    # Add assistant response to history
    history.append({"role": "assistant", "content": answer})
    save_history(session_id, history)

    # 5. Record cost (post-call)
    output_tokens = len(answer.split()) * 2
    check_and_record_cost(0, output_tokens)

    return AskResponse(
        session_id=session_id,
        question=body.question,
        answer=answer,
        history_count=len(history),
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

@app.get("/health", tags=["Ops"])
def health():
    return {
        "status": "ok",
        "uptime": round(time.time() - START_TIME, 1),
        "redis": storage.use_redis
    }

@app.get("/ready", tags=["Ops"])
def ready():
    if not _is_ready:
        raise HTTPException(503, "App not ready")
    
    # Connectivity check
    r = storage.get_redis()
    if not r:
        raise HTTPException(503, "Redis dependency not available")
    
    try:
        r.ping()
    except Exception:
        raise HTTPException(503, "Redis connection lost")
        
    return {"status": "ready", "storage": "redis"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
