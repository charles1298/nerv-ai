// A bolha do chat renderiza LaTeX ($...$) via KaTeX e mais nada: Markdown chega
// cru na tela. Os prompts ja pedem texto limpo, mas modelo nao e' contrato —
// isto cobre o que escapar, o historico ja gravado no banco com marcacao e a
// troca de provedor de IA, que muda o habito de formatacao do modelo.
//
// Nao aplicar dentro de $...$: as chaves e barras do LaTeX sao significativas.
export function limparMarcacao(texto: string): string {
  return texto
    .replace(/^#{1,6}\s+/gm, "")                                   // titulos
    .replace(/\*\*([^*]+)\*\*/g, "$1")                             // negrito
    .replace(/__([^_]+)__/g, "$1")                                 // negrito alternativo
    .replace(/(^|\s)\*(\S[^*\n]*?\S|\S)\*(?=[\s.,;:!?]|$)/g, "$1$2") // italico
    .replace(/`([^`]+)`/g, "$1")                                   // codigo inline
    .replace(/^\s*[-*+]\s+/gm, "• ");                              // marcadores
}
