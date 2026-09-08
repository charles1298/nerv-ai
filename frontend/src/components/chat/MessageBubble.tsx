"use client";

// Bolha de mensagem. O aluno fala em bolha solida; o NERV responde em texto
// solto ao lado do avatar — a conversa fica mais leve, menos "formulario".

import { motion } from "framer-motion";
import { MathRenderer } from "./MathRenderer";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
}

export function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 14, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className={isUser ? "flex justify-end" : "flex items-start gap-3"}
    >
      {!isUser && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src="/nerv-avatar.png"
          alt=""
          width={816}
          height={816}
          loading="lazy"
          className="mt-0.5 size-8 shrink-0"
        />
      )}
      <div
        className={
          isUser
            ? "max-w-[85%] rounded-2xl rounded-br-md bg-primary px-4 py-3 text-sm leading-relaxed text-primary-foreground"
            : "max-w-[85%] text-sm leading-relaxed text-foreground"
        }
      >
        <MathRenderer content={content} />
      </div>
    </motion.div>
  );
}
