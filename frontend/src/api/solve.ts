import apiClient from './client';
import type { SolveResponse } from '../types/api';

export async function solveText(text: string): Promise<SolveResponse> {
  const { data } = await apiClient.post<SolveResponse>('/solve', { text });
  return data;
}

export async function solveUpload(text?: string, image?: File): Promise<SolveResponse> {
  const formData = new FormData();
  if (text) formData.append('text', text);
  if (image) formData.append('image', image);
  const { data } = await apiClient.post<SolveResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function getSolveResult(sessionId: string): Promise<SolveResponse> {
  const { data } = await apiClient.get<SolveResponse>(`/solve/${sessionId}`);
  return data;
}
