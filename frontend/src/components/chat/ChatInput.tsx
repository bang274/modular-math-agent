import React, { useState, useRef, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useSolve } from '../../hooks/useSolve';
import { useChatStore } from '../../store/chatStore';
import type { ChatImage } from '../../types/api';
import './ChatInput.css';

export const ChatInput: React.FC = () => {
  const [text, setText] = useState('');
  const [images, setImages] = useState<ChatImage[]>([]);
  const { solveFromText, solveFromUpload } = useSolve();
  const isLoading = useChatStore((s) => s.isLoading);
  const addMessage = useChatStore((s) => s.addMessage);
  const setLoading = useChatStore((s) => s.setLoading);
  const setError = useChatStore((s) => s.setError);
  const updateMessage = useChatStore((s) => s.updateMessage);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newImages = acceptedFiles.slice(0, 3 - images.length).map((f) => ({
      file: f,
      preview: URL.createObjectURL(f),
    }));
    setImages((prev) => [...prev, ...newImages]);
  }, [images.length]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpeg', '.jpg', '.png', '.webp'] },
    maxFiles: 3,
    maxSize: 10 * 1024 * 1024,
    disabled: isLoading,
  });

  const removeImage = (idx: number) => {
    setImages((prev) => {
      URL.revokeObjectURL(prev[idx].preview);
      return prev.filter((_, i) => i !== idx);
    });
  };

  const handleSend = async () => {
    if ((!text.trim() && images.length === 0) || isLoading) return;

    const userMsgId = Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    const assistantMsgId = Date.now().toString(36) + Math.random().toString(36).slice(2, 8);

    addMessage({
      id: userMsgId,
      role: 'user',
      content: text.trim(),
      images: images.length > 0 ? [...images] : undefined,
      timestamp: Date.now(),
      status: 'success',
    });

    addMessage({
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      status: 'processing',
    });

    setLoading(true);
    setText('');
    setImages([]);

    try {
      let response;
      if (images.length > 0) {
        response = await solveFromUpload(text || undefined, images[0].file);
      } else {
        response = await solveFromText(text);
      }
      updateMessage(assistantMsgId, {
        results: response.results,
        sessionId: response.session_id,
        status: 'success',
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Có lỗi xảy ra';
      updateMessage(assistantMsgId, { status: 'error' });
      setError(message);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input">
      {images.length > 0 && (
        <div className="chat-input__images">
          {images.map((img, idx) => (
            <div key={idx} className="chat-input__image">
              <img src={img.preview} alt={`Upload ${idx + 1}`} />
              <button
                type="button"
                className="chat-input__remove"
                onClick={() => removeImage(idx)}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="chat-input__bar">
        <div {...getRootProps()} className={`chat-input__upload ${isDragActive ? 'active' : ''}`}>
          <input {...getInputProps()} />
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <path d="M21 15l-5-5L5 21" />
          </svg>
        </div>

        <textarea
          ref={textareaRef}
          className="chat-input__textarea"
          placeholder="Nhập đề bài toán..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={isLoading}
        />

        <button
          className="chat-input__send"
          onClick={handleSend}
          disabled={isLoading || (!text.trim() && images.length === 0)}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>
    </div>
  );
};
