# Contributing Guide

## Git Workflow

```
main ← develop ← feature/person-X-module-name
```

### Branch Naming
- `feature/person-1-extractor-ocr`
- `feature/person-2-wolfram-tool`
- `feature/person-3-agent-graph`
- `feature/person-4-redis-cache`
- `feature/person-5-api-endpoints`
- `feature/person-6-upload-ui`

### Rules
1. Mỗi người work trên branch riêng
2. PR vào `develop` cần ít nhất 1 review
3. Shared interfaces (`app/models/`, `frontend/src/types/`) — thảo luận trước khi sửa
4. Resolve conflicts ở branch cá nhân trước khi PR

## Module Ownership

| Person | Owns | Do NOT modify |
|--------|------|---------------|
| 1 | `app/agent/nodes/extractor.py`, `app/utils/image.py`, `app/utils/validators.py` | Tools, API, Graph |
| 2 | `app/tools/*` | Agent nodes, API |
| 3 | `app/agent/graph.py`, `app/agent/state.py`, `app/agent/nodes/classifier.py`, `easy_solver.py`, `hard_solver.py`, `aggregator.py`, `app/agent/edges/*` | Tools, Cache, API |
| 4 | `app/cache/*`, `app/db/*`, `app/agent/nodes/cache_node.py` | Tools, Agent logic |
| 5 | `app/api/*`, `app/main.py`, `app/config.py`, `app/telemetry/*`, `app/models/request.py`, `app/models/response.py`, `docker-compose.yml` | Agent nodes, Tools |
| 6 | `frontend/src/*` | Backend |

### Shared (discuss before editing)
- `app/models/common.py` — Enums used everywhere
- `app/models/problem.py` — Core data model
- `app/llm/prompts.py` — Each person edits their section only
- `app/llm/provider.py` — LLM factory
- `.env.example` — Environment variables

## Code Style

### Backend
- Python 3.11+, type hints everywhere
- Formatter: `ruff format`
- Linter: `ruff check`
- Docstrings: Google style
- Async-first: use `async/await`

### Frontend
- TypeScript strict mode
- Functional components + hooks
- CSS Modules or co-located CSS files
- No `any` types

## Testing

```bash
# Backend
cd backend && python -m pytest tests/ -v

# Frontend (when tests exist)
cd frontend && npm run test
```

Write tests for:
- Happy path
- Error cases
- Edge cases (empty input, timeouts, rate limits)
- Mock external APIs (Groq, Wolfram, Tavily, Redis)
