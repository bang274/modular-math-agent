/**
 * Custom hook for solving math problems.
 */
import { useCallback } from 'react';
import { solveText, solveUpload } from '../api/solve';
import { useSolveStore } from '../store/solveStore';

export function useSolve() {
  const { setLoading, setResponse, setError, reset } = useSolveStore();

  const solveFromText = useCallback(async (text: string) => {
    reset();
    setLoading(true);
    try {
      const response = await solveText(text);
      setResponse(response);
      return response;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [reset, setLoading, setResponse, setError]);

  const solveFromUpload = useCallback(async (text?: string, image?: File) => {
    reset();
    setLoading(true);
    try {
      const response = await solveUpload(text, image);
      setResponse(response);
      return response;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [reset, setLoading, setResponse, setError]);

  return { solveFromText, solveFromUpload, reset };
}
