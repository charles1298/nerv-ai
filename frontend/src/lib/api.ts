// Cliente HTTP do backend NERV AI — injeta o JWT do Zustand em toda chamada.

import { useAuthStore } from "@/store/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = useAuthStore.getState().accessToken;
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { detail?: string };
    // Token expirado/inválido: limpa a sessão e volta pro login em vez de
    // mostrar um erro genérico em cada tela. Só age se havia token (sessão ativa).
    if (res.status === 401 && token) {
      useAuthStore.getState().logout();
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    throw new ApiError(res.status, body.detail ?? `Erro ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

export interface UserPublic {
  id: string;
  school_id: string | null;
  name: string;
  email: string;
  role: "student" | "teacher" | "manager" | "admin";
  grade: string | null;
}

export interface SessionPublic {
  id: string;
  subject_id: string | null;
  topic_id: string | null;
  started_at: string;
  ended_at: string | null;
}

export interface MessagePublic {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface SubjectPublic {
  id: string;
  name: string;
  bncc_code: string | null;
}

export interface TopicPublic {
  id: string;
  subject_id: string;
  name: string;
  bncc_skill_code: string | null;
}

export interface ExercisePublic {
  id: string;
  question: string;
  tipo: string;
  difficulty: number;
  alternatives: { label: string; text: string }[];
  hints: string[];
}

export interface AttemptResult {
  attempt_id: string;
  is_correct: boolean;
  score: number;
  feedback: string;
  step_by_step_solution: string;
}

export interface GamificationState {
  xp_total: number;
  streak_days: number;
  last_activity_date: string | null;
  badges: { id: string; name: string }[];
}

export interface EssayPublic {
  id: string;
  theme: string;
  content: string;
  nota_total: number | null;
  notas_por_criterio: Record<string, number> | null;
  analise_detalhada: {
    pontos_fortes: string[];
    pontos_fracos: string[];
    erros_gramaticais: { trecho: string; erro: string; correcao: string }[];
  } | null;
  reescrita_sugerida: string | null;
  nota_estimada_real_enem: string | null;
  proximos_passos: string[] | null;
  submitted_at: string;
}

export interface StudentCard {
  student_id: string;
  name: string;
  grade: string | null;
  status: "em_dia" | "atencao" | "critico";
  sessions_count: number;
  exercises_attempted: number;
  correct_rate: number | null;
  mastered_topics: string[];
  struggling_topics: string[];
  best_essay_score: number | null;
  last_session_at: string | null;
}

export interface SchoolOverview {
  students_count: number;
  active_students_last_7_days: number;
  heatmap: { grade: string | null; subject: string; attempts: number; correct_rate: number | null }[];
}

export interface BnccDiagnostic {
  subject: string;
  bncc_code: string | null;
  topics_total: number;
  topics_mastered: number;
  mastery_pct: number;
}

export interface StudentReport {
  student: { id: string; name: string; grade: string | null };
  aggregates: Record<string, unknown>;
  status: string;
  narrative: {
    resumo: string;
    evolucao: string;
    pontos_fortes: string[];
    pontos_atencao: string[];
    recomendacoes: string[];
    proximos_topicos: string[];
  } | null;
}

export interface UploadResult {
  upload_id: string;
  url: string;
  analysis: string;
}

export const api = {
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<UserPublic>("/students/me"),
  createSession: (subjectId?: string, topicId?: string) =>
    request<SessionPublic>("/sessions", {
      method: "POST",
      body: JSON.stringify({ subject_id: subjectId ?? null, topic_id: topicId ?? null }),
    }),
  getMessages: (sessionId: string) =>
    request<MessagePublic[]>(`/sessions/${sessionId}/messages`),
  listSubjects: () => request<SubjectPublic[]>("/subjects"),
  listTopics: (subjectId: string) =>
    request<TopicPublic[]>(`/subjects/${subjectId}/topics`),
  listExercises: () => request<ExercisePublic[]>("/exercises"),
  generateExercise: (topicId: string) =>
    request<ExercisePublic>("/exercises/generate", {
      method: "POST",
      body: JSON.stringify({ topic_id: topicId, tipo: "multipla_escolha" }),
    }),
  attemptExercise: (exerciseId: string, answer: string, timeSpentSeconds: number) =>
    request<AttemptResult>(`/exercises/${exerciseId}/attempt`, {
      method: "POST",
      body: JSON.stringify({ answer, time_spent_seconds: timeSpentSeconds }),
    }),
  endSession: (sessionId: string) =>
    request<SessionPublic>(`/sessions/${sessionId}/end`, { method: "POST" }),
  myGamification: () => request<GamificationState>("/gamification/me"),
  submitEssay: (theme: string, content: string) =>
    request<EssayPublic>("/redacoes", {
      method: "POST",
      body: JSON.stringify({ theme, content }),
    }),
  listEssays: () => request<EssayPublic[]>("/redacoes"),
  classDashboard: () => request<StudentCard[]>("/reports/turma"),
  studentReport: (studentId: string) => request<StudentReport>(`/reports/aluno/${studentId}`),
  schoolOverview: () => request<SchoolOverview>("/reports/escola"),
  bnccDiagnostic: () => request<BnccDiagnostic[]>("/reports/bncc"),
  exportMyData: () => request<Record<string, unknown>>("/lgpd/export"),
};

/** Upload de foto (multipart) com análise por visão. */
export async function uploadImage(
  file: File,
  prompt: string,
  sessionId?: string,
): Promise<UploadResult> {
  const token = useAuthStore.getState().accessToken;
  const form = new FormData();
  form.append("file", file);
  form.append("prompt", prompt);
  if (sessionId) form.append("session_id", sessionId);

  const res = await fetch(`${API_URL}/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new ApiError(res.status, body.detail ?? `Erro ${res.status}`);
  }
  return res.json() as Promise<UploadResult>;
}

/**
 * Streaming SSE do chat de tutoria.
 * Chama onChunk a cada token do Fable 5 e resolve quando o stream termina.
 */
export async function streamChat(
  sessionId: string,
  content: string,
  onChunk: (text: string) => void,
): Promise<void> {
  const token = useAuthStore.getState().accessToken;
  const res = await fetch(`${API_URL}/sessions/${sessionId}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  });
  if (!res.ok || !res.body) {
    throw new ApiError(res.status, "Falha ao iniciar o stream de tutoria");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Frames SSE são separados por linha em branco
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const dataLine = frame.split("\n").find((l) => l.startsWith("data: "));
      if (!dataLine) continue;
      const payload = dataLine.slice(6);
      if (payload === "[DONE]") return;
      if (frame.includes("event: error")) {
        throw new ApiError(500, payload);
      }
      const parsed = JSON.parse(payload) as { text: string };
      onChunk(parsed.text);
    }
  }
}
