# API Endpoints

**Base URL:** `/api/v1`  
**Backend:** `http://localhost:8000`

## REST

| Method | Endpoint | Usage |
|--------|----------|-------|
| `POST` | `/solve` | Solve math problem from text input |
| `POST` | `/upload` | Solve math problem from image upload (multipart) |
| `GET` | `/solve/:sessionId` | Fetch solve result by session ID |
| `GET` | `/history` | List paginated solve sessions |
| `GET` | `/history/:sessionId` | Get detail of a specific session |

## WebSocket

| Protocol | Endpoint | Usage |
|----------|----------|-------|
| `WS/WSS` | `/ws/:sessionId` | Real-time streaming of solve progress and results |
| | **Send:** `{ action: "solve", text?, image_b64? }` | Trigger solve over WebSocket |
| | **Receive:** `WSMessage` (type: connected, processing, extraction_complete, solving_problem, tool_called, problem_solved, all_complete, error, pong) | Live status updates |

## Input Sources

| Module | File |
|--------|------|
| Chat input (textarea + multi-image) | `src/components/chat/ChatInput.tsx` |
| Upload form (textarea + single image) | `src/components/upload/UploadZone.tsx` |

Both route through `useSolve()` → `api/solve.ts` → `api/client.ts`
