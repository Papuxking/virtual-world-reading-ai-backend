"""Condiciones de logros evaluadas a partir de sesiones confirmadas en BD."""
from collections import Counter
from models import AchievementCatalog, PlayerAchievement, PlayerAnswer, PlayerSession, PlayerTypologyProgress
from game_rules import DIFFICULTY_ORDER

NAMES = {'first_reading': 'Primera lectura', 'explorer': 'Explorador', 'avid_reader': 'Lector ávido',
         'perfectionist': 'Perfeccionista', 'star_literal': 'Estrella literal',
         'star_inferencial': 'Estrella inferencial', 'star_critico': 'Estrella crítica',
         'improvement': 'En mejora', 'centurion': 'Centurión', 'half_millennium': 'Medio milenio'}


def eligible_achievements(db, user_id, slot_id):
    sessions = db.query(PlayerSession).filter_by(user_id=user_id, slot_id=slot_id).order_by(PlayerSession.id).all()
    levels = Counter(level for (level,) in db.query(PlayerAnswer.comprehension_level).join(PlayerSession)
                     .filter(PlayerSession.user_id == user_id, PlayerSession.slot_id == slot_id,
                             PlayerAnswer.is_correct.is_(True)).all())
    rows = db.query(PlayerTypologyProgress).filter_by(user_id=user_id, slot_id=slot_id).all()
    total = sum(r.best_score for r in rows if r.typology in DIFFICULTY_ORDER)
    previous, improved = {}, False
    for session in sessions:
        if session.typology in previous and session.session_score > previous[session.typology]:
            improved = True
        previous[session.typology] = max(previous.get(session.typology, 0), session.session_score)
    conditions = {'first_reading': bool(sessions), 'avid_reader': len(sessions) >= 4,
                  'explorer': set(DIFFICULTY_ORDER).issubset({s.typology for s in sessions}),
                  'perfectionist': any(s.is_perfect for s in sessions), 'improvement': improved,
                  'centurion': total >= 100, 'half_millennium': total >= 500,
                  'star_literal': levels['Literal'] >= 6, 'star_inferencial': levels['Inferencial'] >= 6,
                  'star_critico': levels['Critico'] >= 6}
    return {key for key, valid in conditions.items() if valid}


def grant_achievements(db, user_id, slot_id):
    existing = {a.achievement_id for a in db.query(PlayerAchievement).filter_by(user_id=user_id, slot_id=slot_id).all()}
    for key in eligible_achievements(db, user_id, slot_id) - existing:
        catalog = db.get(AchievementCatalog, key)
        if catalog is not None and not catalog.is_active:
            continue
        db.add(PlayerAchievement(user_id=user_id, slot_id=slot_id, achievement_id=key,
                                 achievement_name=catalog.name if catalog else NAMES[key]))
    db.flush()
