# Deployment Information — Production AI Agent

## Public URL
- **Railway:** https://zealous-grace-production-0630.up.railway.app
- **Render:** https://ai-agent-ihdp.onrender.com/

## Platform
- Railway / Render

## Test Commands

### 1. Health & Readiness Check
```bash
# Liveness
curl https://zealous-grace-production-0630.up.railway.app/health

# Readiness (checks Redis connection)
curl https://zealous-grace-production-0630.up.railway.app/ready
```

### 2. API Test (Requires API Key)
Lấy `AGENT_API_KEY` từ dashboard environment variables.

```bash
curl -X POST https://zealous-grace-production-0630.up.railway.app/ask \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Docker?",
    "session_id": "test-session-001"
  }'
```

### 3. Rate Limiting Test
Chạy lệnh này liên tục 15 lần:
```bash
for i in {1..15}; do 
  curl -s -o /dev/null -w "%{http_code}\n" \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -X POST https://zealous-grace-production-0630.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'; 
done
# Sẽ xuất hiện lỗi 429 sau 10 request.
```

## Environment Variables Set
- `PORT`: 8000
- `REDIS_URL`: `redis://...` (Railway/Render internal URL)
- `AGENT_API_KEY`: `your-secure-key`
- `ENVIRONMENT`: `production`
- `LLM_MODEL`: `gpt-4o-mini`
- `DAILY_BUDGET_USD`: `1.0`

## Screenshots
Các ảnh chụp màn hình nằm trong thư mục gốc của repo:
- [railway.png](railway.png)
- [render.png](render.png)
