/**
 * Zustand store for solve state management.
 * Person 6 owns this file.
 */
import { create } from 'zustand';
import type { ProblemResult, SolveResponse, WSMessage } from '../types/api';

interface SolveState {
  // State
  isLoading: boolean;
  sessionId: string | null;
  results: ProblemResult[];
  totalProblems: number;
  solvedCount: number;
  failedCount: number;
  cachedCount: number;
  totalLatencyMs: number;
  status: string;
  error: string | null;
  wsMessages: WSMessage[];

  // Actions
  setLoading: (loading: boolean) => void;
  setResponse: (response: SolveResponse) => void;
  addWSMessage: (message: WSMessage) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  isLoading: false,
  sessionId: null,
  results: [],
  totalProblems: 0,
  solvedCount: 0,
  failedCount: 0,
  cachedCount: 0,
  totalLatencyMs: 0,
  status: '',
  error: null,
  wsMessages: [],
};

export const useSolveStore = create<SolveState>((set) => ({
  ...initialState,

  setLoading: (isLoading) => set({ isLoading }),

  setResponse: (response) =>
    set({
      sessionId: response.session_id,
      results: response.results,
      totalProblems: response.total_problems,
      solvedCount: response.solved_count,
      failedCount: response.failed_count,
      cachedCount: response.cached_count,
      totalLatencyMs: response.total_latency_ms,
      status: response.status,
      isLoading: false,
      error: null,
    }),

  addWSMessage: (message) =>
    set((state) => ({ wsMessages: [...state.wsMessages, message] })),

  setError: (error) => set({ error, isLoading: false }),

  reset: () => set(initialState),
}));
