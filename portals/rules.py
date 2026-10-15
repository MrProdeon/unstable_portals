"""Правила: какие действия логичны для портала в его текущем состоянии."""
from dataclasses import dataclass
from datetime import timedelta

STABILIZE = "stabilize"
CLOSE = "close"
OBSERVER = "observer"
QUESTION = "question"
UNMARK = "unmark"


@dataclass
class ActionState:
    allowed: bool = True
    reason: str = ""                 # почему действие запрещено
    needs_confirmation: bool = False
    warning: str = ""                # текст предупреждения для подтверждения


def _blocked(reason):
    return ActionState(allowed=False, reason=reason)


def evaluate(portal, action):
    """Возвращает ActionState для пары (портал, действие)."""
    if not portal.is_open:
        return _blocked("портал закрыт, любые действия с ним невозможны.")

    left = portal.time_left
    collapsed = left is not None and left <= timedelta(0)

    if action == STABILIZE:
        if collapsed:
            return _blocked("портал уже схлопнулся, стабилизировать поздно. "
                            "Его можно только закрыть.")
        if portal.stability >= 100:
            return _blocked("портал уже полностью стабилен.")

    elif action == OBSERVER:
        if collapsed:
            return _blocked("портал уже схлопнулся, наблюдателю там нечего делать.")
        if portal.risk.level == "critical":
            return _blocked(
                f"критический риск ({portal.risk.score}): отправлять наблюдателя "
                "слишком опасно. Сначала стабилизируйте портал или закройте его."
            )

    elif action == QUESTION:
        if portal.under_question:
            return _blocked("портал уже помечен как «под вопросом».")

    elif action == UNMARK:
        if not portal.under_question:
            return _blocked("у портала нет отметки «под вопросом».")

    elif action == CLOSE:
        if portal.creatures_count:
            return ActionState(
                needs_confirmation=True,
                warning=(f"Внутри осталось существ: {portal.creatures_count}. "
                         "При закрытии они останутся внутри. "
                         "Поставьте галочку, чтобы подтвердить закрытие."),
            )

    return ActionState()