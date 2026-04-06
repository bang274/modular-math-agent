import { create } from 'zustand';
import type { ChatMessage, Conversation, ProblemResult } from '../types/api';

interface ChatState {
  conversations: Conversation[];
  activeId: string | null;
  isLoading: boolean;
  error: string | null;

  addMessage: (msg: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  setActive: (id: string) => void;
  newConversation: () => string;
  deleteConversation: (id: string) => void;
  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
  setResults: (results: ProblemResult[], sessionId: string) => void;
}

function makeId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

function makeTitle(content: string) {
  return content.trim().slice(0, 40) || 'Cuộc trò chuyện mới';
}

const STORAGE_KEY = 'math-chat-conversations';

function loadConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return parsed.map((c: Conversation) => ({
      ...c,
      messages: c.messages.map((m) => ({ ...m, images: m.images ? m.images.map((img) => ({ ...img, file: undefined as unknown as File })) : undefined })),
    }));
  } catch {
    return [];
  }
}

function saveConversations(convs: Conversation[]) {
  try {
    const serializable = convs.map((c) => ({
      ...c,
      messages: c.messages.map((m) => ({ ...m, images: m.images ? m.images.map((img) => ({ preview: img.preview })) : undefined })),
    }));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(serializable));
  } catch { /* quota exceeded */ }
}

const initial = loadConversations();

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: initial,
  activeId: initial.length > 0 ? initial[initial.length - 1].id : null,
  isLoading: false,
  error: null,

  addMessage: (msg) =>
    set((state) => {
      const convs = state.conversations.map((c) => {
        if (c.id !== state.activeId) return c;
        const updated = { ...c, messages: [...c.messages, msg], updatedAt: Date.now() };
        if (c.messages.length === 0 && msg.role === 'user') {
          updated.title = makeTitle(msg.content);
        }
        return updated;
      });
      saveConversations(convs);
      return { conversations: convs };
    }),

  updateMessage: (id, updates) =>
    set((state) => {
      const convs = state.conversations.map((c) => {
        if (c.id !== state.activeId) return c;
        return {
          ...c,
          messages: c.messages.map((m) => (m.id === id ? { ...m, ...updates } : m)),
        };
      });
      saveConversations(convs);
      return { conversations: convs };
    }),

  setActive: (id) => set({ activeId: id }),

  newConversation: () => {
    const id = makeId();
    const conv: Conversation = {
      id,
      title: 'Cuộc trò chuyện mới',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    set((state) => {
      const convs = [...state.conversations, conv];
      saveConversations(convs);
      return { conversations: convs, activeId: id };
    });
    return id;
  },

  deleteConversation: (id) =>
    set((state) => {
      const convs = state.conversations.filter((c) => c.id !== id);
      saveConversations(convs);
      return {
        conversations: convs,
        activeId: state.activeId === id ? (convs.length > 0 ? convs[convs.length - 1].id : null) : state.activeId,
      };
    }),

  setLoading: (v) => set({ isLoading: v }),

  setError: (e) => set({ error: e, isLoading: false }),

  setResults: (results, sessionId) =>
    set((state) => {
      const convs = state.conversations.map((c) => {
        if (c.id !== state.activeId) return c;
        const msgs = c.messages.map((m) => {
          if (m.role === 'assistant' && m.status === 'processing') {
            return { ...m, results, sessionId, status: 'success' as const };
          }
          return m;
        });
        return { ...c, messages: msgs, sessionId, updatedAt: Date.now() };
      });
      saveConversations(convs);
      return { conversations: convs, isLoading: false };
    }),
}));
