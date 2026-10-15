"""Расчёт риска портала и рекомендуемого действия.

Модуль не зависит от моделей: принимает обычные числа,
поэтому его легко тестировать отдельно.
"""
from dataclasses import dataclass, field
from datetime import timedelta

WEIGHT_STABILITY = 0.4
WEIGHT_ENERGY = 0.3
WEIGHT_TIME = 0.3

TIME_HORIZON_HOURS = 72   # дальше этого срока время риск не повышает
URGENT_HOURS = 6          # «схлопнется совсем скоро»

LOW_LIMIT = 30            # < 30  -> низкий
CRITICAL_LIMIT = 60       # >= 60 -> критический


@dataclass
class RiskFactor:
    label: str
    value: int
    weight: float
    contribution: float
    note: str


@dataclass
class RiskAssessment:
    score: int
    level: str            # low / medium / critical / closed
    level_label: str
    factors: list = field(default_factory=list)


@dataclass
class Recommendation:
    code: str             # stabilize / close / observer / question / keep / none
    label: str
    reason: str
    css: str


def time_factor(time_left):
    """0–100: чем меньше времени до схлопывания, тем выше значение."""
    if time_left is None:
        return 0
    hours = time_left.total_seconds() / 3600
    if hours <= 0:
        return 100
    if hours >= TIME_HORIZON_HOURS:
        return 0
    return round(100 * (1 - hours / TIME_HORIZON_HOURS))


def assess_risk(*, stability, energy, time_left, is_open=True):
    if not is_open:
        return RiskAssessment(score=0, level="closed", level_label="Закрыт")

    stability_risk = 100 - stability
    time_risk = time_factor(time_left)

    if time_left is None:
        time_note = "срок схлопывания не задан"
    elif time_risk == 0:
        time_note = f"до схлопывания {TIME_HORIZON_HOURS} ч и более"
    else:
        time_note = f"до схлопывания меньше {TIME_HORIZON_HOURS} ч"

    factors = [
        RiskFactor("Нестабильность", stability_risk, WEIGHT_STABILITY,
                   stability_risk * WEIGHT_STABILITY,
                   f"100 − стабильность ({stability}) = {stability_risk}"),
        RiskFactor("Энергия", energy, WEIGHT_ENERGY,
                   energy * WEIGHT_ENERGY,
                   f"уровень энергии = {energy}"),
        RiskFactor("Нехватка времени", time_risk, WEIGHT_TIME,
                   time_risk * WEIGHT_TIME, time_note),
    ]
    score = max(0, min(100, round(sum(f.contribution for f in factors))))

    if score >= CRITICAL_LIMIT:
        level, label = "critical", "Критический"
    elif score >= LOW_LIMIT:
        level, label = "medium", "Средний"
    else:
        level, label = "low", "Низкий"

    return RiskAssessment(score, level, label, factors)


def recommend(*, risk, time_left, creatures_count, is_open=True):
    if not is_open:
        return Recommendation("none", "Действий не требуется",
                              "Портал уже закрыт.", "closed")

    if time_left is not None and time_left <= timedelta(0):
        return Recommendation("close", "Закрыть портал",
                              "Расчётное время схлопывания уже прошло.",
                              "critical")

    urgent = time_left is not None and time_left <= timedelta(hours=URGENT_HOURS)

    if risk.level == "critical" and urgent:
        reason = (f"Критический риск, до схлопывания меньше {URGENT_HOURS} ч: "
                  "стабилизировать уже не успеть.")
        if creatures_count:
            reason += (f" Внутри существ: {creatures_count}. "
                       "Перед закрытием убедитесь, что они выведены.")
        return Recommendation("close", "Закрыть портал", reason, "critical")

    if risk.level == "critical":
        return Recommendation("stabilize", "Стабилизировать портал",
                              "Критический риск, но время ещё есть: "
                              "портал можно удержать.", "critical")

    if risk.level == "medium":
        if creatures_count:
            return Recommendation(
                "observer", "Отправить наблюдателя",
                f"Средний риск, внутри существ: {creatures_count}. "
                "Нужно проверить обстановку на месте.", "medium")
        return Recommendation(
            "question", "Пометить «под вопросом»",
            "Средний риск, существ внутри нет: достаточно взять портал "
            "на заметку и перепроверить позже.", "medium")

    return Recommendation("keep", "Оставить открытым",
                          "Риск низкий, вмешательство не требуется.", "low")