import apiClient from './client';
import type { HistoryListResponse } from '../types/api';

export async function getHistory(page = 1, pageSize = 20): Promise<HistoryListResponse> {
  const { data } = await apiClient.get<HistoryListResponse>('/history', {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function getSessionDetail(sessionId: string) {
  const { data } = await apiClient.get(`/history/${sessionId}`);
  return data;
}
