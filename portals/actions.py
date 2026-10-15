"""Действия смотрителя над порталом."""
from dataclasses import dataclass
from datetime import timedelta

from . import rules
from .models import Portal

STABILIZE = "stabilize"
CLOSE = "close"
OBSERVER = "observer"
QUESTION = "question"
UNMARK = "unmark"

ACTION_LABELS = {
    STABILIZE: "Стабилизировать портал",
    CLOSE: "Закрыть портал",
    OBSERVER: "Отправить наблюдателя",
    QUESTION: "Пометить «под вопросом»",
    UNMARK: "Снять отметку «под вопросом»",
}

# --- Параметры эффектов --------------------------------------------------
STABILITY_BOOST = 25      # +стабильность за одну стабилизацию
ENERGY_DROP = 15          # −энергия за одну стабилизацию
EXTEND_HOURS = 24         # на сколько часов откладывается схлопывание
OBSERVER_EVACUATES = 3    # сколько существ выводит наблюдатель


class ActionNotAllowed(Exception):
    """Действие запрещено или требует подтверждения."""

    def __init__(self, message, *, is_warning=False):
        super().__init__(message)
        self.message = message
        self.is_warning = is_warning


@dataclass
class ActionResult:
    action: str
    label: str
    message: str
    risk_before: int
    risk_after: int


# --- Обработчики: меняют поля портала, но не сохраняют его ---------------
def _stabilize(portal):
    old_stab, old_energy = portal.stability, portal.energy_level
    portal.stability = min(100, old_stab + STABILITY_BOOST)
    portal.energy_level = max(0, old_energy - ENERGY_DROP)
    text = (f"Стабильность {old_stab} → {portal.stability}, "
            f"энергия {old_energy} → {portal.energy_level}.")
    left = portal.time_left
    if portal.collapse_at is not None and left is not None and left > timedelta(0):
        portal.collapse_at += timedelta(hours=EXTEND_HOURS)
        text += f" Схлопывание отложено на {EXTEND_HOURS} ч."
    return text


def _close(portal):
    text = "Портал закрыт."
    if portal.creatures_count:
        text += f" Внутри осталось существ: {portal.creatures_count}."
    portal.status = Portal.Status.CLOSED
    portal.under_question = False
    return text


def _observer(portal):
    evacuated = min(OBSERVER_EVACUATES, portal.creatures_count)
    if evacuated == 0:
        return "Наблюдатель осмотрел портал: существ внутри нет."
    portal.creatures_count -= evacuated
    return (f"Наблюдатель осмотрел портал и вывел существ: {evacuated}. "
            f"Осталось внутри: {portal.creatures_count}.")


def _question(portal):
    portal.under_question = True
    return "Портал помечен как «под вопросом»."


def _unmark(portal):
    portal.under_question = False
    return "Отметка «под вопросом» снята."


HANDLERS = {
    STABILIZE: _stabilize,
    CLOSE: _close,
    OBSERVER: _observer,
    QUESTION: _question,
    UNMARK: _unmark,
}


# --- Выполнение ----------------------------------------------------------
def _run(portal, action, confirmed):
    handler = HANDLERS.get(action)
    if handler is None:
        raise ActionNotAllowed("Неизвестное действие.")

    state = rules.evaluate(portal, action)
    if not state.allowed:
        raise ActionNotAllowed(state.reason)
    if state.needs_confirmation and not confirmed:
        raise ActionNotAllowed(state.warning, is_warning=True)

    risk_before = portal.risk.score
    label_before = portal.risk.level_label

    details = handler(portal)
    portal.save()          # save() сам запишет изменения в историю портала

    if action == STABILIZE:
        details += (f" Риск: {risk_before} → {portal.risk.score} "
                    f"({label_before} → {portal.risk.level_label}).")

    return ActionResult(action, ACTION_LABELS[action], details,
                        risk_before, portal.risk.score)


def execute(portal, action, confirmed=False):
    return _run(portal, action, confirmed)


def action_states(portal):
    """Данные для кнопок на карточке портала."""
    states = []
    for code, label in ACTION_LABELS.items():
        state = rules.evaluate(portal, code)
        states.append({
            "code": code,
            "label": label,
            "allowed": state.allowed,
            "reason": state.reason,
            "needs_confirmation": state.needs_confirmation,
            "warning": state.warning,
            "recommended": portal.recommendation.code == code,
        })
    return states