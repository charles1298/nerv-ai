"use client";

// Botão de upload de foto no chat — prova/caderno → análise por visão (seção 5.4).

import { useRef, useState } from "react";
import { uploadImage } from "@/lib/api";

interface ImageUploadProps {
  sessionId: string | null;
  disabled: boolean;
  currentPrompt: string;
  onAnalysis: (analysis: string) => void;
  onError: (message: string) => void;
  onUploadStart: () => void;
}

export function ImageUpload({
  sessionId,
  disabled,
  currentPrompt,
  onAnalysis,
  onError,
  onUploadStart,
}: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const handleFile = async (file: File) => {
    setUploading(true);
    onUploadStart();
    try {
      const result = await uploadImage(file, currentPrompt, sessionId ?? undefined);
      onAnalysis(result.analysis);
    } catch {
      onError("Falha ao analisar a imagem. Tente novamente.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void handleFile(file);
        }}
      />
      <button
        type="button"
        title="Enviar foto de prova ou caderno"
        onClick={() => inputRef.current?.click()}
        disabled={disabled || uploading}
        className="rounded-xl border border-nerv-border px-4 text-lg transition hover:border-nerv-purple disabled:opacity-50"
      >
        {uploading ? "⏳" : "📷"}
      </button>
    </>
  );
}
