"""
metrics_router.py — Endpoints de métricas avanzadas para el dashboard admin.
Tiempo de lectura, respuestas, intentos por pregunta, interacciones NPC,
uso de herramientas. Todos con filtros por fecha, jugador y tipología.
Incluye exportación CSV y Excel.
"""
import io
import csv
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc, Integer, case

from database import get_db
from models import (
    User, PlayerSession, PlayerAnswer, SessionTool,
    PlayerTypologyProgress, Question, Reading, NpcInteraction,
)
from schemas import (
    MetricsReadingTimeResponse, MetricPlayerReadingTime, MetricTypologyReadingTime,
    MetricsAnswersResponse, MetricPlayerAnswers, MetricLevelAnswers,
    MetricsQuestionAttemptsResponse, MetricQuestionAttempt,
    MetricsNpcInteractionsResponse, MetricNpcPlayer,
    MetricsToolUsageResponse, MetricToolUsage,
)
from auth import get_current_admin

router = APIRouter(prefix="/admin/metrics", tags=["Métricas y Reportes"])


# ── Helpers de filtro ────────────────────────────────────────────────────────

def _apply_date_filter(query, date_col, date_from, date_to):
    """Aplica filtro de rango de fechas a una query."""
    if date_from:
        query = query.filter(date_col >= date_from)
    if date_to:
        query = query.filter(date_col <= date_to)
    return query


def _apply_session_filters(query, date_from, date_to, player_id, typology):
    """Aplica los filtros comunes a queries basadas en PlayerSession."""
    if date_from:
        query = query.filter(PlayerSession.completed_at >= date_from)
    if date_to:
        query = query.filter(PlayerSession.completed_at <= date_to)
    if player_id:
        query = query.filter(PlayerSession.user_id == player_id)
    if typology:
        query = query.filter(PlayerSession.typology == typology)
    return query


# ── Métricas de Tiempo de Lectura ────────────────────────────────────────────

@router.get("/reading-time", response_model=MetricsReadingTimeResponse)
def get_reading_time_metrics(
    date_from: Optional[datetime] = Query(None, description="Fecha desde (ISO)"),
    date_to: Optional[datetime] = Query(None, description="Fecha hasta (ISO)"),
    player_id: Optional[int] = Query(None, description="Filtrar por jugador"),
    typology: Optional[str] = Query(None, description="Filtrar por tipología"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Tiempo promedio de lectura con desglose por jugador y tipología."""
    base = db.query(PlayerSession).filter(
        PlayerSession.reading_time_seconds.isnot(None),
        PlayerSession.reading_time_seconds > 0,
    )
    base = _apply_session_filters(base, date_from, date_to, player_id, typology)

    # Global
    global_stats = base.with_entities(
        sqlfunc.avg(PlayerSession.reading_time_seconds).label("avg_rt"),
        sqlfunc.avg(PlayerSession.total_time_seconds).label("avg_tt"),
        sqlfunc.count(PlayerSession.id).label("cnt"),
    ).first()

    # Por jugador
    by_player_q = (
        base.join(User, PlayerSession.user_id == User.id)
        .with_entities(
            User.id,
            User.display_name,
            sqlfunc.avg(PlayerSession.reading_time_seconds).label("avg_rt"),
            sqlfunc.avg(PlayerSession.total_time_seconds).label("avg_tt"),
            sqlfunc.count(PlayerSession.id).label("cnt"),
        )
        .group_by(User.id, User.display_name)
        .order_by(sqlfunc.avg(PlayerSession.reading_time_seconds).desc())
        .all()
    )

    # Por tipología
    by_typology_q = (
        base.with_entities(
            PlayerSession.typology,
            sqlfunc.avg(PlayerSession.reading_time_seconds).label("avg_rt"),
            sqlfunc.avg(PlayerSession.total_time_seconds).label("avg_tt"),
            sqlfunc.count(PlayerSession.id).label("cnt"),
        )
        .group_by(PlayerSession.typology)
        .order_by(PlayerSession.typology)
        .all()
    )

    return MetricsReadingTimeResponse(
        avg_reading_time=round(float(global_stats.avg_rt or 0), 1),
        avg_total_time=round(float(global_stats.avg_tt or 0), 1),
        total_sessions=global_stats.cnt or 0,
        by_player=[
            MetricPlayerReadingTime(
                player_id=p[0], display_name=p[1],
                avg_reading_time=round(float(p[2] or 0), 1),
                avg_total_time=round(float(p[3] or 0), 1),
                total_sessions=p[4],
            ) for p in by_player_q
        ],
        by_typology=[
            MetricTypologyReadingTime(
                typology=t[0],
                avg_reading_time=round(float(t[1] or 0), 1),
                avg_total_time=round(float(t[2] or 0), 1),
                total_sessions=t[3],
            ) for t in by_typology_q
        ],
    )


# ── Métricas de Respuestas ───────────────────────────────────────────────────

@router.get("/answers", response_model=MetricsAnswersResponse)
def get_answer_metrics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    player_id: Optional[int] = Query(None),
    typology: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Respuestas correctas e incorrectas con desglose."""
    base = db.query(PlayerAnswer).join(PlayerSession, PlayerAnswer.session_id == PlayerSession.id)
    base = _apply_session_filters(base, date_from, date_to, player_id, typology)

    # Global
    total_correct = base.filter(PlayerAnswer.is_correct == True).count()
    total_incorrect = base.filter(PlayerAnswer.is_correct == False).count()
    total_all = total_correct + total_incorrect
    overall_accuracy = round(total_correct / total_all * 100, 1) if total_all > 0 else 0

    # Por jugador
    by_player_q = (
        base.join(User, PlayerSession.user_id == User.id)
        .with_entities(
            User.id,
            User.display_name,
            sqlfunc.sum(case((PlayerAnswer.is_correct == True, 1), else_=0)).label("correct"),
            sqlfunc.sum(case((PlayerAnswer.is_correct == False, 1), else_=0)).label("incorrect"),
            sqlfunc.count(PlayerAnswer.id).label("total"),
        )
        .group_by(User.id, User.display_name)
        .order_by(User.display_name)
        .all()
    )

    # Por nivel de comprensión
    by_level_q = (
        base.with_entities(
            PlayerAnswer.comprehension_level,
            sqlfunc.sum(case((PlayerAnswer.is_correct == True, 1), else_=0)).label("correct"),
            sqlfunc.sum(case((PlayerAnswer.is_correct == False, 1), else_=0)).label("incorrect"),
            sqlfunc.count(PlayerAnswer.id).label("total"),
        )
        .group_by(PlayerAnswer.comprehension_level)
        .all()
    )

    return MetricsAnswersResponse(
        total_correct=total_correct,
        total_incorrect=total_incorrect,
        overall_accuracy=overall_accuracy,
        by_player=[
            MetricPlayerAnswers(
                player_id=p[0], display_name=p[1],
                total_correct=int(p[2] or 0), total_incorrect=int(p[3] or 0),
                accuracy=round(int(p[2] or 0) / int(p[4]) * 100, 1) if int(p[4]) > 0 else 0,
            ) for p in by_player_q
        ],
        by_level=[
            MetricLevelAnswers(
                level=l[0],
                total_correct=int(l[1] or 0), total_incorrect=int(l[2] or 0),
                accuracy=round(int(l[1] or 0) / int(l[3]) * 100, 1) if int(l[3]) > 0 else 0,
            ) for l in by_level_q
        ],
    )


# ── Intentos por Pregunta ───────────────────────────────────────────────────

@router.get("/question-attempts", response_model=MetricsQuestionAttemptsResponse)
def get_question_attempt_metrics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    player_id: Optional[int] = Query(None),
    typology: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Número de intentos por pregunta con tasa de acierto."""
    base = (
        db.query(PlayerAnswer)
        .join(PlayerSession, PlayerAnswer.session_id == PlayerSession.id)
        .join(Question, PlayerAnswer.question_id == Question.id)
        .join(Reading, Question.reading_id == Reading.id)
    )
    base = _apply_session_filters(base, date_from, date_to, player_id, typology)

    questions_q = (
        base.with_entities(
            Question.id,
            Question.question_text,
            Reading.title,
            Reading.typology,
            Question.comprehension_level,
            sqlfunc.count(PlayerAnswer.id).label("attempts"),
            sqlfunc.sum(case((PlayerAnswer.is_correct == True, 1), else_=0)).label("correct"),
            sqlfunc.sum(case((PlayerAnswer.is_correct == False, 1), else_=0)).label("incorrect"),
        )
        .group_by(Question.id, Question.question_text, Reading.title, Reading.typology, Question.comprehension_level)
        .order_by(sqlfunc.count(PlayerAnswer.id).desc())
        .limit(limit)
        .all()
    )

    return MetricsQuestionAttemptsResponse(
        questions=[
            MetricQuestionAttempt(
                question_id=q[0],
                question_text=q[1][:120] + "..." if len(q[1]) > 120 else q[1],
                reading_title=q[2],
                typology=q[3],
                comprehension_level=q[4],
                total_attempts=q[5],
                correct_count=int(q[6] or 0),
                incorrect_count=int(q[7] or 0),
                correct_rate=round(int(q[6] or 0) / q[5] * 100, 1) if q[5] > 0 else 0,
            ) for q in questions_q
        ],
        total_questions=len(questions_q),
    )


# ── Interacciones NPC ────────────────────────────────────────────────────────

@router.get("/npc-interactions", response_model=MetricsNpcInteractionsResponse)
def get_npc_interaction_metrics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    player_id: Optional[int] = Query(None),
    npc_type: Optional[str] = Query(None, description="Filtrar: 'robot' o 'sabio'"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Métricas de interacciones con NPCs (robot asistente y sabio)."""
    base = db.query(NpcInteraction)
    base = _apply_date_filter(base, NpcInteraction.created_at, date_from, date_to)
    if player_id:
        base = base.filter(NpcInteraction.user_id == player_id)
    if npc_type:
        base = base.filter(NpcInteraction.npc_type == npc_type)

    total_robot = base.filter(NpcInteraction.npc_type == "robot").count() if not npc_type or npc_type == "robot" else 0
    total_sabio = base.filter(NpcInteraction.npc_type == "sabio").count() if not npc_type or npc_type == "sabio" else 0

    # Por jugador
    by_player_q = (
        base.join(User, NpcInteraction.user_id == User.id)
        .with_entities(
            User.id,
            User.display_name,
            sqlfunc.sum(case((NpcInteraction.npc_type == "robot", 1), else_=0)).label("robot"),
            sqlfunc.sum(case((NpcInteraction.npc_type == "sabio", 1), else_=0)).label("sabio"),
            sqlfunc.count(NpcInteraction.id).label("total"),
        )
        .group_by(User.id, User.display_name)
        .order_by(sqlfunc.count(NpcInteraction.id).desc())
        .all()
    )

    return MetricsNpcInteractionsResponse(
        total_robot=total_robot,
        total_sabio=total_sabio,
        total_all=total_robot + total_sabio,
        by_player=[
            MetricNpcPlayer(
                player_id=p[0], display_name=p[1],
                robot_interactions=int(p[2] or 0),
                sabio_interactions=int(p[3] or 0),
                total_interactions=int(p[4] or 0),
            ) for p in by_player_q
        ],
    )


# ── Uso de Herramientas ─────────────────────────────────────────────────────

@router.get("/tool-usage", response_model=MetricsToolUsageResponse)
def get_tool_usage_metrics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    player_id: Optional[int] = Query(None),
    typology: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Frecuencia y tipo de uso de herramientas."""
    base = (
        db.query(SessionTool)
        .join(PlayerSession, SessionTool.session_id == PlayerSession.id)
    )
    base = _apply_session_filters(base, date_from, date_to, player_id, typology)

    total_sessions_q = (
        db.query(sqlfunc.count(sqlfunc.distinct(PlayerSession.id)))
        .filter(PlayerSession.id.in_(
            base.with_entities(SessionTool.session_id).distinct()
        ))
        .scalar()
    )

    tools_q = (
        base.with_entities(
            SessionTool.tool_name,
            sqlfunc.count(SessionTool.id).label("total"),
            sqlfunc.sum(case((SessionTool.was_used == True, 1), else_=0)).label("used"),
        )
        .group_by(SessionTool.tool_name)
        .order_by(SessionTool.tool_name)
        .all()
    )

    return MetricsToolUsageResponse(
        tools=[
            MetricToolUsage(
                tool_name=t[0],
                total_sessions=int(t[1] or 0),
                times_used=int(t[2] or 0),
                usage_rate=round(int(t[2] or 0) / int(t[1]) * 100, 1) if int(t[1]) > 0 else 0,
            ) for t in tools_q
        ],
        total_sessions=total_sessions_q or 0,
    )


# ── Exportación CSV ──────────────────────────────────────────────────────────

@router.get("/export/csv")
def export_metrics_csv(
    metric: str = Query(..., description="Métrica: reading-time, answers, npc-interactions, tool-usage"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    player_id: Optional[int] = Query(None),
    typology: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Exporta métricas en formato CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    if metric == "reading-time":
        data = get_reading_time_metrics(date_from, date_to, player_id, typology, admin, db)
        writer.writerow(["Jugador", "Tiempo Lectura Prom (s)", "Tiempo Total Prom (s)", "Sesiones"])
        for p in data.by_player:
            writer.writerow([p.display_name, p.avg_reading_time, p.avg_total_time, p.total_sessions])

    elif metric == "answers":
        data = get_answer_metrics(date_from, date_to, player_id, typology, admin, db)
        writer.writerow(["Jugador", "Correctas", "Incorrectas", "Precisión (%)"])
        for p in data.by_player:
            writer.writerow([p.display_name, p.total_correct, p.total_incorrect, p.accuracy])

    elif metric == "npc-interactions":
        data = get_npc_interaction_metrics(date_from, date_to, player_id, None, admin, db)
        writer.writerow(["Jugador", "Robot", "Sabio", "Total"])
        for p in data.by_player:
            writer.writerow([p.display_name, p.robot_interactions, p.sabio_interactions, p.total_interactions])

    elif metric == "tool-usage":
        data = get_tool_usage_metrics(date_from, date_to, player_id, typology, admin, db)
        writer.writerow(["Herramienta", "Sesiones Totales", "Veces Usada", "Tasa de Uso (%)"])
        for t in data.tools:
            writer.writerow([t.tool_name, t.total_sessions, t.times_used, t.usage_rate])

    elif metric == "question-attempts":
        data = get_question_attempt_metrics(date_from, date_to, player_id, typology, 200, admin, db)
        writer.writerow(["Pregunta", "Lectura", "Tipología", "Nivel", "Intentos", "Correctas", "Incorrectas", "Tasa Acierto (%)"])
        for q in data.questions:
            writer.writerow([q.question_text, q.reading_title, q.typology, q.comprehension_level, q.total_attempts, q.correct_count, q.incorrect_count, q.correct_rate])

    else:
        raise HTTPException(status_code=400, detail=f"Métrica desconocida: {metric}")

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="metricas_{metric}.csv"'},
    )


# ── Exportación Excel ────────────────────────────────────────────────────────

@router.get("/export/excel")
def export_metrics_excel(
    metric: str = Query(..., description="Métrica: reading-time, answers, npc-interactions, tool-usage"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    player_id: Optional[int] = Query(None),
    typology: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Exporta métricas en formato Excel (.xlsx)."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl no está instalado en el servidor")

    wb = Workbook()
    ws = wb.active
    ws.title = metric

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="6366F1", end_color="6366F1", fill_type="solid")

    if metric == "reading-time":
        data = get_reading_time_metrics(date_from, date_to, player_id, typology, admin, db)
        headers = ["Jugador", "Tiempo Lectura Prom (s)", "Tiempo Total Prom (s)", "Sesiones"]
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
        for i, p in enumerate(data.by_player, 2):
            ws.cell(row=i, column=1, value=p.display_name)
            ws.cell(row=i, column=2, value=p.avg_reading_time)
            ws.cell(row=i, column=3, value=p.avg_total_time)
            ws.cell(row=i, column=4, value=p.total_sessions)

    elif metric == "answers":
        data = get_answer_metrics(date_from, date_to, player_id, typology, admin, db)
        headers = ["Jugador", "Correctas", "Incorrectas", "Precisión (%)"]
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
        for i, p in enumerate(data.by_player, 2):
            ws.cell(row=i, column=1, value=p.display_name)
            ws.cell(row=i, column=2, value=p.total_correct)
            ws.cell(row=i, column=3, value=p.total_incorrect)
            ws.cell(row=i, column=4, value=p.accuracy)

    elif metric == "npc-interactions":
        data = get_npc_interaction_metrics(date_from, date_to, player_id, None, admin, db)
        headers = ["Jugador", "Robot", "Sabio", "Total"]
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
        for i, p in enumerate(data.by_player, 2):
            ws.cell(row=i, column=1, value=p.display_name)
            ws.cell(row=i, column=2, value=p.robot_interactions)
            ws.cell(row=i, column=3, value=p.sabio_interactions)
            ws.cell(row=i, column=4, value=p.total_interactions)

    elif metric == "tool-usage":
        data = get_tool_usage_metrics(date_from, date_to, player_id, typology, admin, db)
        headers = ["Herramienta", "Sesiones Totales", "Veces Usada", "Tasa de Uso (%)"]
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
        for i, t in enumerate(data.tools, 2):
            ws.cell(row=i, column=1, value=t.tool_name)
            ws.cell(row=i, column=2, value=t.total_sessions)
            ws.cell(row=i, column=3, value=t.times_used)
            ws.cell(row=i, column=4, value=t.usage_rate)

    elif metric == "question-attempts":
        data = get_question_attempt_metrics(date_from, date_to, player_id, typology, 200, admin, db)
        headers = ["Pregunta", "Lectura", "Tipología", "Nivel", "Intentos", "Correctas", "Incorrectas", "Tasa Acierto (%)"]
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
        for i, q in enumerate(data.questions, 2):
            ws.cell(row=i, column=1, value=q.question_text)
            ws.cell(row=i, column=2, value=q.reading_title)
            ws.cell(row=i, column=3, value=q.typology)
            ws.cell(row=i, column=4, value=q.comprehension_level)
            ws.cell(row=i, column=5, value=q.total_attempts)
            ws.cell(row=i, column=6, value=q.correct_count)
            ws.cell(row=i, column=7, value=q.incorrect_count)
            ws.cell(row=i, column=8, value=q.correct_rate)

    else:
        raise HTTPException(status_code=400, detail=f"Métrica desconocida: {metric}")

    # Ajustar anchos de columna
    for col in ws.columns:
        max_length = 0
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 4, 40)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="metricas_{metric}.xlsx"'},
    )
