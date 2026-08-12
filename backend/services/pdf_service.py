"""Geração de PDF dos relatórios pedagógicos (seções 5.5 e 7.3).

Usa ReportLab — Python puro, sem dependências de sistema (roda igual no Windows
de dev e no container do Railway). Este módulo só diagrama: todos os números
chegam prontos de `routers/reports.py`, que é quem fala com o banco.

Layout é claro (fundo branco), não o dark mode do app: estes PDFs são impressos
para reuniões pedagógicas.
"""

from datetime import datetime, timedelta, timezone
from io import BytesIO
from xml.sax.saxutils import escape

import structlog
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = structlog.get_logger()

# Paleta do NERV (seção 7.1) adaptada para impressão: o roxo é da marca, o neon
# vira verde escuro porque #39FF14 é ilegível sobre branco.
PURPLE = colors.HexColor("#7C3AED")
GREEN = colors.HexColor("#15803D")
YELLOW = colors.HexColor("#B45309")
RED = colors.HexColor("#B91C1C")
GREY = colors.HexColor("#6B7280")
LIGHT = colors.HexColor("#F3F4F6")

STATUS_LABEL = {"em_dia": "Em dia", "atencao": "Atenção", "critico": "Crítico"}
STATUS_COLOR = {"em_dia": GREEN, "atencao": YELLOW, "critico": RED}

# Brasília é UTC-3 fixo desde a extinção do horário de verão (2019), então o
# offset constante evita depender do tzdata da IANA, ausente no Windows.
BRASILIA = timezone(timedelta(hours=-3))


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "NervTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=PURPLE,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "NervSubtitle",
            parent=base["Normal"],
            fontSize=10,
            textColor=GREY,
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "NervH2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=PURPLE,
            spaceBefore=12,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "NervBody", parent=base["BodyText"], fontSize=10, leading=14, spaceAfter=4
        ),
        "bullet": ParagraphStyle(
            "NervBullet",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            leftIndent=10,
            bulletIndent=2,
            spaceAfter=2,
        ),
        "muted": ParagraphStyle(
            "NervMuted", parent=base["BodyText"], fontSize=9, textColor=GREY, leading=12
        ),
    }


def _footer(canvas, doc) -> None:
    """Rodapé com origem do documento e número da página, em toda página."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    gerado = datetime.now(BRASILIA).strftime("%d/%m/%Y às %H:%M")
    canvas.drawString(20 * mm, 12 * mm, f"NERV AI — gerado em {gerado} (horário de Brasília)")
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"página {doc.page}")
    canvas.setStrokeColor(LIGHT)
    canvas.line(20 * mm, 15 * mm, A4[0] - 20 * mm, 15 * mm)
    canvas.restoreState()


def _doc(buffer: BytesIO, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=22 * mm,
        title=title,
        author="NERV AI",
    )


def _bullets(items: list[str], style: ParagraphStyle) -> list[Paragraph]:
    """Lista com marcador. Texto do modelo/banco é escapado — `&` e `<` quebrariam
    o mini-HTML que o Paragraph interpreta."""
    return [Paragraph(escape(str(item)), style, bulletText="•") for item in items]


def _pct(rate: float | None) -> str:
    return f"{round(rate * 100)}%" if rate is not None else "—"


def _date_br(iso: str | None) -> str:
    if not iso:
        return "nunca"
    try:
        return datetime.fromisoformat(iso).astimezone(BRASILIA).strftime("%d/%m/%Y")
    except ValueError:
        return "—"


def _rate_color(rate: float | None) -> colors.Color:
    if rate is None:
        return LIGHT
    if rate >= 0.7:
        return colors.HexColor("#DCFCE7")
    if rate >= 0.4:
        return colors.HexColor("#FEF3C7")
    return colors.HexColor("#FEE2E2")


def _table(data: list[list], widths: list[float], align_right_from: int | None = None) -> Table:
    table = Table(data, colWidths=widths, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]
    if align_right_from is not None:
        style.append(("ALIGN", (align_right_from, 1), (-1, -1), "RIGHT"))
    table.setStyle(TableStyle(style))
    return table


def student_report_pdf(
    student: dict, aggregates: dict, status: str, narrative: dict | None
) -> bytes:
    """Relatório individual do aluno em PDF (seção 7.2).

    `narrative` é None quando o modelo falhou — o PDF sai só com os quantitativos,
    que são a fonte da verdade.
    """
    styles = _styles()
    buffer = BytesIO()
    doc = _doc(buffer, f"Relatório — {student['name']}")

    story: list = [
        Paragraph("Relatório Pedagógico", styles["title"]),
        Paragraph(
            f"{escape(student['name'])} · {escape(student.get('grade') or 'série não informada')}",
            styles["subtitle"],
        ),
    ]

    status_txt = STATUS_LABEL.get(status, status)
    resumo = _table(
        [
            ["Indicador", "Valor"],
            ["Situação", status_txt],
            ["Sessões de tutoria", str(aggregates["sessions_count"])],
            ["Última sessão", _date_br(aggregates["last_session_at"])],
            [
                "Exercícios respondidos",
                f"{aggregates['exercises_attempted']} "
                f"({aggregates['exercises_correct']} corretos)",
            ],
            ["Taxa de acerto", _pct(aggregates["correct_rate"])],
            [
                "Nota média",
                f"{aggregates['avg_score']:.1f}" if aggregates["avg_score"] is not None else "—",
            ],
            [
                "Melhor redação",
                str(aggregates["best_essay_score"])
                if aggregates["best_essay_score"] is not None
                else "—",
            ],
        ],
        widths=[65 * mm, 60 * mm],
    )
    resumo.setStyle(
        TableStyle([("TEXTCOLOR", (1, 1), (1, 1), STATUS_COLOR.get(status, colors.black))])
    )
    story += [Paragraph("Panorama", styles["h2"]), resumo]

    for titulo, topicos in (
        ("Tópicos dominados", aggregates["mastered_topics"]),
        ("Tópicos em dificuldade", aggregates["struggling_topics"]),
    ):
        story.append(Paragraph(titulo, styles["h2"]))
        if topicos:
            story += _bullets(topicos, styles["bullet"])
        else:
            story.append(Paragraph("Nenhum registrado até aqui.", styles["muted"]))

    if narrative:
        blocos: list = [Paragraph("Análise pedagógica", styles["h2"])]
        if narrative.get("resumo"):
            blocos.append(Paragraph(escape(narrative["resumo"]), styles["body"]))
        if narrative.get("evolucao"):
            blocos.append(Paragraph(escape(narrative["evolucao"]), styles["body"]))
        story.append(KeepTogether(blocos))

        for titulo, chave in (
            ("Pontos fortes", "pontos_fortes"),
            ("Pontos de atenção", "pontos_atencao"),
            ("Recomendações para o professor", "recomendacoes"),
            ("Próximos tópicos sugeridos", "proximos_topicos"),
        ):
            itens = narrative.get(chave) or []
            if itens:
                story.append(
                    KeepTogether(
                        [Paragraph(titulo, styles["h2"]), *_bullets(itens, styles["bullet"])]
                    )
                )
    else:
        story += [
            Paragraph("Análise pedagógica", styles["h2"]),
            Paragraph(
                "Narrativa indisponível nesta geração. Os dados quantitativos acima "
                "vêm direto do banco e permanecem válidos.",
                styles["muted"],
            ),
        ]

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    logger.info("student_report_pdf_generated", student_id=student["id"])
    return buffer.getvalue()


def school_overview_pdf(school_name: str, overview: dict, bncc: list[dict]) -> bytes:
    """Visão da escola em PDF para reuniões pedagógicas (seção 7.3)."""
    styles = _styles()
    buffer = BytesIO()
    doc = _doc(buffer, f"Visão da escola — {school_name}")

    story: list = [
        Paragraph("Visão da Escola", styles["title"]),
        Paragraph(escape(school_name), styles["subtitle"]),
        Paragraph("Panorama", styles["h2"]),
        _table(
            [
                ["Indicador", "Valor"],
                ["Alunos cadastrados", str(overview["students_count"])],
                ["Ativos nos últimos 7 dias", str(overview["active_students_last_7_days"])],
            ],
            widths=[65 * mm, 60 * mm],
        ),
        Paragraph("Desempenho por série e matéria", styles["h2"]),
    ]

    heatmap = overview["heatmap"]
    if heatmap:
        linhas = [["Série", "Matéria", "Tentativas", "Taxa de acerto"]]
        for row in heatmap:
            linhas.append(
                [
                    escape(row["grade"] or "—"),
                    escape(row["subject"]),
                    str(row["attempts"]),
                    _pct(row["correct_rate"]),
                ]
            )
        tabela = _table(linhas, widths=[35 * mm, 60 * mm, 30 * mm, 35 * mm], align_right_from=2)
        # Mapa de calor: a própria célula da taxa carrega a cor (seção 7.3).
        tabela.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (3, i + 1), (3, i + 1), _rate_color(row["correct_rate"]))
                    for i, row in enumerate(heatmap)
                ]
            )
        )
        story.append(tabela)
    else:
        story.append(Paragraph("Sem tentativas registradas ainda.", styles["muted"]))

    if bncc:
        story += [PageBreak(), Paragraph("Diagnóstico BNCC", styles["h2"])]
        linhas = [["Matéria", "Código", "Tópicos", "Dominados", "% domínio"]]
        for item in bncc:
            linhas.append(
                [
                    escape(item["subject"]),
                    escape(item["bncc_code"] or "—"),
                    str(item["topics_total"]),
                    str(item["topics_mastered"]),
                    f"{item['mastery_pct']}%",
                ]
            )
        story.append(
            _table(linhas, widths=[55 * mm, 25 * mm, 25 * mm, 30 * mm, 30 * mm], align_right_from=2)
        )

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    logger.info("school_overview_pdf_generated", school=school_name)
    return buffer.getvalue()
