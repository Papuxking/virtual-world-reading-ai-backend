"""Asignación, corrección y puntuación autoritativas. No acepta aciertos del cliente."""
import secrets
import uuid
from collections import Counter
from fastapi import HTTPException
from models import GameAttempt, PlayerSlot, PlayerTypologyProgress, Question
from game_rules import DIFFICULTY_ORDER, MAX_INTENTOS_POR_TIPOLOGIA
from progression import ensure_typology_rows, agotada

LEVELS = ('Literal', 'Inferencial', 'Critico')
POINTS = {'Literal': 10, 'Inferencial': 20, 'Critico': 30}
PENALTIES = {'Literal': 3, 'Inferencial': 5, 'Critico': 8}


def active_slot_locked(db, user_id):
    slot = db.query(PlayerSlot).filter_by(user_id=user_id, is_active=True).with_for_update().first()
    if slot is None:
        raise HTTPException(409, 'No hay una partida activa')
    return slot


def latest_attempt(db, user_id, slot_id, reading_id, attempt_id=None):
    query = db.query(GameAttempt).filter_by(user_id=user_id, slot_id=slot_id, reading_id=reading_id)
    if attempt_id:
        query = query.filter_by(id=attempt_id)
    else:
        query = query.filter_by(finalized=False)
    return query.order_by(GameAttempt.created_at.desc()).with_for_update().first()


def start_attempt(db, user_id, reading, reuse=True):
    slot = active_slot_locked(db, user_id)
    existing = latest_attempt(db, user_id, slot.id, reading.id)
    if reuse and existing:
        return existing
    rows = {r.typology: r for r in ensure_typology_rows(db, user_id, slot.id)}
    progress = rows.get(reading.typology)
    if progress is None or not progress.is_unlocked:
        raise HTTPException(403, 'TYPOLOGY_LOCKED')
    if agotada(progress):
        raise HTTPException(403, 'SIN_INTENTOS')
    # Límite también para tipologías aprobadas: nunca más de cinco sesiones.
    if progress.attempts_used >= MAX_INTENTOS_POR_TIPOLOGIA:
        raise HTTPException(403, 'SIN_INTENTOS')
    questions = db.query(Question).filter_by(reading_id=reading.id).order_by(Question.question_number).all()
    assigned = []
    for level in LEVELS:
        available = [q.id for q in questions if q.comprehension_level == level]
        if len(available) < 2:
            raise HTTPException(409, 'La lectura no tiene suficientes preguntas por nivel')
        assigned.extend(secrets.SystemRandom().sample(available, 2))
    attempt = GameAttempt(id=str(uuid.uuid4()), user_id=user_id, slot_id=slot.id, reading_id=reading.id,
                          question_ids=assigned, results=[])
    db.add(attempt)
    db.flush()
    return attempt


def assigned_payload(db, user_id, reading):
    attempt = start_attempt(db, user_id, reading)
    questions = {q.id: q for q in reading.questions}
    data = {key: getattr(reading, key) for key in ('id', 'title', 'typology', 'type', 'content', 'created_at', 'updated_at')}
    data['attempt_id'] = attempt.id
    data['questions'] = [{
        'id': q.id, 'question_number': q.question_number, 'comprehension_level': q.comprehension_level,
        'question_text': q.question_text,
        'answers': [{'letter': a.letter, 'answer_text': a.answer_text} for a in q.answers],
    } for q in (questions[qid] for qid in attempt.question_ids)]
    db.commit()
    return data


def grade_answer(db, user_id, reading_id, question_id, letter, attempt_id=None):
    slot = active_slot_locked(db, user_id)
    attempt = latest_attempt(db, user_id, slot.id, reading_id, attempt_id)
    if attempt is None or attempt.finalized:
        raise HTTPException(409, 'Inicia o reanuda la lectura antes de responder')
    question = db.get(Question, question_id)
    if question_id not in attempt.question_ids or question is None or question.reading_id != reading_id:
        raise HTTPException(403, 'La pregunta no pertenece al intento')
    for result in attempt.results:
        if result['question_id'] == question_id:
            if result['letter_selected'] != letter:
                raise HTTPException(409, 'La respuesta ya está confirmada')
            return result
    counts = Counter(r['level'] for r in attempt.results)
    expected = next((level for level in LEVELS if counts[level] < 2), None)
    if question.comprehension_level != expected:
        raise HTTPException(409, 'Completa las preguntas del nivel actual')
    if letter not in {a.letter for a in question.answers}:
        raise HTTPException(422, 'Respuesta no permitida')
    correct = letter == question.correct_answer
    result = {'question_id': question_id, 'level': question.comprehension_level,
              'letter_selected': letter, 'correct': correct,
              'correct_answer': question.correct_answer, 'justification': question.justification or '',
              'points_earned': POINTS[expected] if correct else 0,
              'penalty': 0 if correct else PENALTIES[expected]}
    attempt.results = [*attempt.results, result]
    db.flush()
    return result


def score_results(results, tool_names=(), complete=True):
    score = 0
    for level in LEVELS:
        group = [r for r in results if r['level'] == level]
        for result in group:
            score = score + POINTS[level] if result['correct'] else max(0, score - PENALTIES[level])
        if len(group) == 2 and all(r['correct'] for r in group):
            score += 15
    bonus = 20 * len(set(tool_names) & {'highlight', 'underline', 'notes'})
    if complete:
        score += 50 + (25 if results and all(r['correct'] for r in results) else 0) + bonus
    return score, bonus
