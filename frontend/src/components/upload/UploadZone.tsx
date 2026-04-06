/**
 * UploadZone — Drag & drop + text input for math problems.
 * Person 6 owns this file.
 */
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useSolve } from '../../hooks/useSolve';
import { useSolveStore } from '../../store/solveStore';
import './UploadZone.css';

export const UploadZone: React.FC = () => {
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const { solveFromText, solveFromUpload } = useSolve();
  const isLoading = useSolveStore((s) => s.isLoading);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const f = acceptedFiles[0];
    if (f) {
      setFile(f);
      const reader = new FileReader();
      reader.onload = () => setPreview(reader.result as string);
      reader.readAsDataURL(f);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpeg', '.jpg', '.png', '.webp'] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
    disabled: isLoading,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() && !file) return;

    try {
      if (file) {
        await solveFromUpload(text || undefined, file);
      } else {
        await solveFromText(text);
      }
    } catch {
      // Error handled by store
    }
  };

  const handleClear = () => {
    setText('');
    setFile(null);
    setPreview(null);
  };

  return (
    <form className="upload-zone" onSubmit={handleSubmit}>
      <div className="upload-zone__text">
        <label htmlFor="math-input" className="upload-label">
          📝 Nhập đề bài (text)
        </label>
        <textarea
          id="math-input"
          className="upload-textarea"
          placeholder="Ví dụ: Tính tích phân ∫₀¹ x² dx, hoặc dán LaTeX..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={5}
          disabled={isLoading}
        />
      </div>

      <div className="upload-divider">
        <span>hoặc</span>
      </div>

      <div
        {...getRootProps()}
        className={`upload-dropzone ${isDragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
      >
        <input {...getInputProps()} id="image-upload" />
        {preview ? (
          <div className="upload-preview">
            <img src={preview} alt="Preview" className="upload-preview__img" />
            <button
              type="button"
              className="upload-preview__remove"
              onClick={(e) => { e.stopPropagation(); handleClear(); }}
            >
              ✕
            </button>
          </div>
        ) : (
          <div className="upload-dropzone__content">
            <span className="upload-icon">📷</span>
            <p>Kéo thả ảnh đề bài vào đây</p>
            <p className="upload-hint">PNG, JPG, WebP — tối đa 10MB</p>
          </div>
        )}
      </div>

      <div className="upload-actions">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isLoading || (!text.trim() && !file)}
        >
          {isLoading ? (
            <><span className="spinner" /> Đang giải...</>
          ) : (
            <>🚀 Giải bài</>
          )}
        </button>
        {(text || file) && (
          <button type="button" className="btn btn-ghost" onClick={handleClear}>
            Xóa
          </button>
        )}
      </div>
    </form>
  );
};
