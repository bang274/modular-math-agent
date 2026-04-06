import { useState, useEffect, useCallback } from 'react';
import { getHistory } from '../api/history';
import type { HistoryItem } from '../types/api';

export function useHistory() {
  const [sessions, setSessions] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const fetch = useCallback(async (p: number = 1) => {
    setLoading(true);
    try {
      const data = await getHistory(p);
      setSessions(data.sessions);
      setTotal(data.total);
      setPage(p);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch(1); }, [fetch]);

  return { sessions, total, page, loading, fetchPage: fetch };
}
