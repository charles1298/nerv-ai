"use client";

import { MathRenderer } from "./MathRenderer";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
}

export function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-nerv-purple text-white"
            : "border border-nerv-border bg-nerv-surface text-nerv-text"
        }`}
      >
        {!isUser && (
          <p className="mb-1 font-display text-xs font-bold text-nerv-neon">NERV</p>
        )}
        <MathRenderer content={content} />
      </div>
    </div>
  );
}
