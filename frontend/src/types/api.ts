/**
 * Shared TypeScript types — mirrors backend Pydantic schemas.
 */

export type Difficulty = 'easy' | 'hard' | 'unknown';

export type SolveRoute =
  | 'llm_direct'
  | 'web_search'
  | 'wolfram'
  | 'python_sandbox'
  | 'fallback_search'
  | 'cached';

export type SessionStatus =
  | 'uploaded'
  | 'processing'
  | 'completed'
  | 'partial'
  | 'failed';

export type WSMessageType =
  | 'connected'
  | 'processing'
  | 'extraction_complete'
  | 'solving_problem'
  | 'tool_called'
  | 'problem_solved'
  | 'all_complete'
  | 'error'
  | 'pong';

export type MessageRole = 'user' | 'assistant';
export type MessageStatus = 'pending' | 'processing' | 'success' | 'error';

export interface Problem {
  id: number;
  content: string;
  original_text?: string;
  source: 'text' | 'image' | 'both';
}

export interface SolutionStep {
  step: number;
  description: string;
  latex: string;
}

export interface ToolTrace {
  route: SolveRoute;
  tools_used: string[];
  attempts: number;
  cache_hit: boolean;
  latency_ms: number;
  errors: string[];
}

export interface ProblemResult {
  problem_id: number;
  original: string;
  difficulty: Difficulty;
  steps: SolutionStep[];
  final_answer: string;
  confidence: number;
  tool_trace: ToolTrace;
  error?: string | null;
}

export interface SolveResponse {
  session_id: string;
  status: SessionStatus;
  ws_url?: string;
  results: ProblemResult[];
  total_problems: number;
  solved_count: number;
  failed_count: number;
  cached_count: number;
  total_latency_ms: number;
}

export interface HistoryItem {
  session_id: string;
  created_at: string;
  problem_count: number;
  solved_count: number;
  preview: string;
}

export interface HistoryListResponse {
  sessions: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  redis_connected: boolean;
  db_connected: boolean;
}

export interface WSMessage {
  type: WSMessageType;
  data: Record<string, unknown>;
}

export interface ChatImage {
  file: File;
  preview: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  images?: ChatImage[];
  timestamp: number;
  status: MessageStatus;
  results?: ProblemResult[];
  sessionId?: string;
  error?: string | null;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
  sessionId?: string;
}
