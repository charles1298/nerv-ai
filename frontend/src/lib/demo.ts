// Modo demonstração — permite que o site funcione publicamente (Vercel) SEM backend.
// Ativado por NEXT_PUBLIC_DEMO_MODE=true. Em desenvolvimento local (sem essa flag),
// o app usa o backend real normalmente. Todos os dados aqui são fictícios.

export const DEMO = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

const DEMO_USER_KEY = "nerv-demo-user";

interface DemoUser {
  id: string;
  school_id: string | null;
  name: string;
  email: string;
  role: "student" | "teacher" | "manager" | "admin";
  grade: string | null;
}

function classifyUser(email: string): DemoUser {
  const e = (email || "").toLowerCase();
  if (e.includes("prof"))
    return { id: "t-1", school_id: "s-1", name: "Prof. Carla Souza", email, role: "teacher", grade: null };
  if (e.includes("gestor") || e.includes("admin") || e.includes("diretor"))
    return { id: "m-1", school_id: "s-1", name: "Direção — Escola Demo", email, role: "admin", grade: null };
  return {
    id: "a-1",
    school_id: "s-1",
    name: "João Pereira",
    email: email || "aluno@demo.nerv.ai",
    role: "student",
    grade: "9ano_ef",
  };
}

function saveDemoUser(u: DemoUser) {
  if (typeof window !== "undefined") localStorage.setItem(DEMO_USER_KEY, JSON.stringify(u));
}
function loadDemoUser(): DemoUser {
  if (typeof window !== "undefined") {
    const raw = localStorage.getItem(DEMO_USER_KEY);
    if (raw) {
      try {
        return JSON.parse(raw) as DemoUser;
      } catch {
        /* ignore */
      }
    }
  }
  return classifyUser("aluno@demo.nerv.ai");
}

const SUBJECTS = [
  { id: "sub-mat", name: "Matemática", bncc_code: "MT" },
  { id: "sub-lp", name: "Língua Portuguesa", bncc_code: "LP" },
  { id: "sub-ci", name: "Ciências", bncc_code: "CN" },
];

const TOPICS: Record<string, { id: string; subject_id: string; name: string; bncc_skill_code: string }[]> = {
  "sub-mat": [
    { id: "top-func", subject_id: "sub-mat", name: "Funções quadráticas", bncc_skill_code: "EF09MA06" },
    { id: "top-porc", subject_id: "sub-mat", name: "Porcentagem e juros simples", bncc_skill_code: "EF09MA05" },
    { id: "top-pit", subject_id: "sub-mat", name: "Teorema de Pitágoras", bncc_skill_code: "EF09MA13" },
  ],
  "sub-lp": [
    { id: "top-interp", subject_id: "sub-lp", name: "Interpretação de texto", bncc_skill_code: "EF89LP33" },
    { id: "top-fig", subject_id: "sub-lp", name: "Figuras de linguagem", bncc_skill_code: "EF89LP37" },
  ],
  "sub-ci": [
    { id: "top-sol", subject_id: "sub-ci", name: "Sistema solar", bncc_skill_code: "EF09CI14" },
    { id: "top-cad", subject_id: "sub-ci", name: "Cadeias alimentares", bncc_skill_code: "EF06CI04" },
  ],
};

const DEMO_EXERCISE = {
  id: "ex-demo-1",
  question:
    "Uma loja aumentou o preço de um produto de R$ 80,00 para R$ 100,00. Qual foi o percentual de aumento aplicado?",
  tipo: "multipla_escolha",
  difficulty: 2,
  alternatives: [
    { label: "A", text: "15%" },
    { label: "B", text: "25%" },
    { label: "C", text: "20%" },
    { label: "D", text: "30%" },
  ],
  hints: ["Aumento percentual $= \\frac{\\text{novo} - \\text{antigo}}{\\text{antigo}} \\times 100$."],
};

const DEMO_SOLUTION =
  "Passo 1: variação = 100 − 80 = 20.\nPasso 2: $\\frac{20}{80} = 0{,}25$.\nPasso 3: $0{,}25 \\times 100 = 25\\%$.\nLogo, o aumento foi de 25% (alternativa B).";

function evaluationFor(theme: string, content: string) {
  return {
    id: "essay-" + Date.now(),
    theme,
    content,
    nota_total: 760,
    notas_por_criterio: { C1: 160, C2: 200, C3: 160, C4: 160, C5: 80 },
    analise_detalhada: {
      pontos_fortes: ["Repertório sociocultural pertinente", "Tese clara logo na introdução"],
      pontos_fracos: ["Proposta de intervenção pouco detalhada"],
      erros_gramaticais: [
        { trecho: "a nível de", erro: "expressão inadequada", correcao: "em nível de / no âmbito de" },
      ],
    },
    reescrita_sugerida:
      "Portanto, cabe ao Estado, em parceria com as escolas, promover campanhas educativas contínuas, a fim de garantir a efetividade da proposta.",
    nota_estimada_real_enem: "Entre 720 e 800",
    proximos_passos: ["Detalhar a proposta de intervenção: agente, ação, meio/modo e finalidade."],
    submitted_at: new Date().toISOString(),
  };
}

const PRIOR_ESSAYS = [
  {
    id: "essay-prev-2",
    theme: "Caminhos para combater a evasão escolar no Brasil",
    content: "",
    nota_total: 720,
    notas_por_criterio: { C1: 160, C2: 160, C3: 160, C4: 160, C5: 80 },
    analise_detalhada: null,
    reescrita_sugerida: null,
    nota_estimada_real_enem: "Entre 680 e 760",
    proximos_passos: null,
    submitted_at: "2026-06-28T14:00:00Z",
  },
  {
    id: "essay-prev-1",
    theme: "Desafios da inclusão digital nas escolas públicas",
    content: "",
    nota_total: 680,
    notas_por_criterio: { C1: 120, C2: 160, C3: 160, C4: 160, C5: 80 },
    analise_detalhada: null,
    reescrita_sugerida: null,
    nota_estimada_real_enem: "Entre 640 e 720",
    proximos_passos: null,
    submitted_at: "2026-06-20T14:00:00Z",
  },
];

const CLASS_CARDS = [
  {
    student_id: "a-1",
    name: "João Pereira",
    grade: "9ano_ef",
    status: "em_dia" as const,
    sessions_count: 12,
    exercises_attempted: 34,
    correct_rate: 0.79,
    mastered_topics: ["Porcentagem e juros simples"],
    struggling_topics: [],
    best_essay_score: 760,
    last_session_at: "2026-07-06T18:00:00Z",
  },
  {
    student_id: "a-2",
    name: "Maria Fernandes",
    grade: "9ano_ef",
    status: "atencao" as const,
    sessions_count: 5,
    exercises_attempted: 18,
    correct_rate: 0.55,
    mastered_topics: [],
    struggling_topics: ["Funções quadráticas"],
    best_essay_score: 620,
    last_session_at: "2026-07-01T18:00:00Z",
  },
  {
    student_id: "a-3",
    name: "Pedro Almeida",
    grade: "9ano_ef",
    status: "critico" as const,
    sessions_count: 1,
    exercises_attempted: 4,
    correct_rate: 0.25,
    mastered_topics: [],
    struggling_topics: ["Teorema de Pitágoras", "Funções quadráticas"],
    best_essay_score: null,
    last_session_at: null,
  },
];

function reportFor(studentId: string) {
  const card = CLASS_CARDS.find((c) => c.student_id === studentId) ?? CLASS_CARDS[0];
  return {
    student: { id: card.student_id, name: card.name, grade: card.grade },
    aggregates: {
      sessions_count: card.sessions_count,
      exercises_attempted: card.exercises_attempted,
      correct_rate: card.correct_rate,
      mastered_topics: card.mastered_topics,
      struggling_topics: card.struggling_topics,
    },
    status: card.status,
    narrative: {
      resumo: `${card.name} apresenta desempenho ${card.status === "em_dia" ? "consistente" : "que requer atenção"} no período analisado.`,
      evolucao:
        card.status === "em_dia"
          ? "Evolução positiva nas últimas semanas, com aumento da taxa de acerto."
          : "Frequência de estudo abaixo do esperado; recomenda-se acompanhamento próximo.",
      pontos_fortes: card.mastered_topics.length ? [`Domínio em ${card.mastered_topics.join(", ")}`] : ["Engajamento inicial na plataforma"],
      pontos_atencao: card.struggling_topics.length ? [`Dificuldade em ${card.struggling_topics.join(", ")}`] : ["Manter a regularidade dos estudos"],
      recomendacoes: ["Propor lista dirigida nos tópicos de maior dificuldade", "Agendar sessão de tutoria guiada"],
      proximos_topicos: card.struggling_topics.length ? card.struggling_topics : ["Funções quadráticas"],
    },
  };
}

const SCHOOL_OVERVIEW = {
  students_count: 32,
  active_students_last_7_days: 21,
  heatmap: [
    { grade: "9ano_ef", subject: "Matemática", attempts: 210, correct_rate: 0.72 },
    { grade: "9ano_ef", subject: "Língua Portuguesa", attempts: 156, correct_rate: 0.81 },
    { grade: "9ano_ef", subject: "Ciências", attempts: 98, correct_rate: 0.64 },
    { grade: "8ano_ef", subject: "Matemática", attempts: 140, correct_rate: 0.58 },
  ],
};

const BNCC_DIAG = [
  { subject: "Matemática", bncc_code: "MT", topics_total: 4, topics_mastered: 2, mastery_pct: 50.0 },
  { subject: "Língua Portuguesa", bncc_code: "LP", topics_total: 3, topics_mastered: 2, mastery_pct: 66.7 },
  { subject: "Ciências", bncc_code: "CN", topics_total: 3, topics_mastered: 1, mastery_pct: 33.3 },
];

const GAMIFICATION = {
  xp_total: 480,
  streak_days: 5,
  last_activity_date: new Date().toISOString().slice(0, 10),
  badges: [
    { id: "primeira_sessao", name: "Início de Jornada" },
    { id: "matematico", name: "Mente Matemática" },
  ],
};

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

/** Roteia uma chamada de API para dados de demonstração. */
export async function demoRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const body = init.body ? (JSON.parse(init.body as string) as Record<string, unknown>) : {};
  await delay(180); // pequena latência simulada

  if (path === "/auth/login" && method === "POST") {
    saveDemoUser(classifyUser(String(body.email ?? "")));
    return { access_token: "demo-token", refresh_token: "demo-refresh" } as T;
  }
  if (path === "/auth/refresh") return { access_token: "demo-token", refresh_token: "demo-refresh" } as T;
  if (path === "/students/me") return loadDemoUser() as T;

  if (path === "/subjects") return SUBJECTS as T;
  if (path.startsWith("/subjects/") && path.endsWith("/topics")) {
    const sid = path.split("/")[2];
    return (TOPICS[sid] ?? []) as T;
  }

  if (path === "/sessions" && method === "POST")
    return { id: "sess-demo", subject_id: null, topic_id: null, started_at: new Date().toISOString(), ended_at: null } as T;
  if (path.endsWith("/messages")) return [] as T;
  if (path.endsWith("/end")) return { id: "sess-demo", subject_id: null, topic_id: null, started_at: new Date().toISOString(), ended_at: new Date().toISOString() } as T;

  if (path === "/exercises") return [] as T;
  if (path === "/exercises/generate") return DEMO_EXERCISE as T;
  if (path.startsWith("/exercises/") && path.endsWith("/attempt")) {
    const correct = String(body.answer ?? "").trim().toUpperCase() === "B";
    return {
      attempt_id: "att-" + Date.now(),
      is_correct: correct,
      score: correct ? 10 : 0,
      feedback: correct
        ? "Resposta correta! O aumento percentual é calculado sobre o valor inicial."
        : "Ainda não. Lembre que o percentual é calculado sobre o valor ANTIGO (R$ 80), não sobre o novo.",
      step_by_step_solution: DEMO_SOLUTION,
    } as T;
  }

  if (path === "/gamification/me") return GAMIFICATION as T;

  if (path === "/redacoes" && method === "POST")
    return evaluationFor(String(body.theme ?? ""), String(body.content ?? "")) as T;
  if (path === "/redacoes") return PRIOR_ESSAYS as T;

  if (path === "/reports/turma") return CLASS_CARDS as T;
  if (path.startsWith("/reports/aluno/")) return reportFor(path.split("/")[3]) as T;
  if (path === "/reports/escola") return SCHOOL_OVERVIEW as T;
  if (path === "/reports/bncc") return BNCC_DIAG as T;

  if (path === "/lgpd/export") return { user: loadDemoUser(), aviso: "Exportação de demonstração." } as T;

  return {} as T;
}

/** Streaming de tutoria simulado. */
export async function demoStreamChat(content: string, onChunk: (t: string) => void): Promise<void> {
  const reply =
    `Ótima pergunta! Vamos pensar juntos sobre "${content.slice(0, 60)}". ` +
    "Em vez de te dar a resposta pronta, deixa eu te guiar: primeiro, identifique o que o problema está pedindo. " +
    "Por exemplo, em matemática, uma variação percentual é sempre calculada sobre o valor inicial: " +
    "$\\text{variação} = \\frac{\\text{final} - \\text{inicial}}{\\text{inicial}} \\times 100$. " +
    "Tenta aplicar isso e me diz o que encontrou — estou aqui pra ajudar no seu ritmo. 😊 " +
    "(modo demonstração: resposta ilustrativa, sem IA conectada)";
  const words = reply.split(" ");
  for (const w of words) {
    onChunk(w + " ");
    await delay(28);
  }
}

/** Upload de imagem simulado. */
export async function demoUpload(): Promise<{ upload_id: string; url: string; analysis: string }> {
  await delay(500);
  return {
    upload_id: "up-demo",
    url: "",
    analysis:
      "Identifiquei um exercício de matemática sobre porcentagem. Vamos resolver por partes: o aumento é calculado sobre o valor inicial. " +
      "(modo demonstração: análise ilustrativa, sem IA de visão conectada.)",
  };
}
