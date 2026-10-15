from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.functional import cached_property

from . import services

TRACKED_FIELDS = (
    "name",
    "destination_world",
    "energy_level",
    "stability",
    "creatures_count",
    "status",
    "collapse_at",
    "under_question",
)


class Portal(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        CLOSED = "closed", "Закрыт"

    name = models.CharField("Название портала", max_length=100, unique=True)
    destination_world = models.CharField("Мир назначения", max_length=100)
    energy_level = models.PositiveSmallIntegerField(
        "Уровень энергии", default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="От 0 до 100",
    )
    stability = models.PositiveSmallIntegerField(
        "Стабильность", default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="От 0 (схлопнется) до 100 (полностью стабилен)",
    )
    creatures_count = models.PositiveIntegerField(
        "Количество существ внутри", default=0
    )
    status = models.CharField(
        "Статус", max_length=10, choices=Status.choices, default=Status.OPEN
    )
    collapse_at = models.DateTimeField(
        "Время схлопывания", null=True, blank=True,
        help_text="Когда портал схлопнется. Пусто — срок неизвестен.",
    )
    under_question = models.BooleanField("Под вопросом", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Портал"
        verbose_name_plural = "Порталы"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} → {self.destination_world}"

    # --- История изменений ------------------------------------------------
    def _display_value(self, field_name, value):
        if value is None or value == "":
            return "—"
        if field_name == "status":
            return dict(self.Status.choices).get(value, value)
        if field_name == "collapse_at":
            return timezone.localtime(value).strftime("%d.%m.%Y %H:%M")
        if field_name == "under_question":
            return "Да" if value else "Нет"
        return str(value)


    @transaction.atomic
    def save(self, *args, **kwargs):
        old = None
        if not self._state.adding:
            old = Portal.objects.filter(pk=self.pk).first()

        super().save(*args, **kwargs)
        self.reset_assessment()

        if old is None:
            PortalHistory.objects.create(
                portal=self, is_creation=True, field_label="Портал создан"
            )
            return

        for name in TRACKED_FIELDS:
            old_value, new_value = getattr(old, name), getattr(self, name)
            if old_value != new_value:
                PortalHistory.objects.create(
                    portal=self,
                    field_label=str(self._meta.get_field(name).verbose_name),
                    old_value=self._display_value(name, old_value),
                    new_value=self._display_value(name, new_value),
                )

    # --- Время, риск, рекомендация ---------------------------------------
    @property
    def is_open(self):
        return self.status == self.Status.OPEN

    @property
    def time_left(self):
        if self.collapse_at is None:
            return None
        return self.collapse_at - timezone.now()

    @property
    def time_left_display(self):
        if not self.is_open:
            return "—"
        delta = self.time_left
        if delta is None:
            return "Не задано"
        seconds = int(delta.total_seconds())
        if seconds <= 0:
            return "Схлопнулся"
        days, rest = divmod(seconds, 86400)
        hours, rest = divmod(rest, 3600)
        minutes = rest // 60
        parts = []
        if days:
            parts.append(f"{days} д")
        if hours or days:
            parts.append(f"{hours} ч")
        parts.append(f"{minutes} мин")
        return " ".join(parts)

    @cached_property
    def risk(self):
        return services.assess_risk(
            stability=self.stability,
            energy=self.energy_level,
            time_left=self.time_left,
            is_open=self.is_open,
        )

    @cached_property
    def recommendation(self):
        return services.recommend(
            risk=self.risk,
            time_left=self.time_left,
            creatures_count=self.creatures_count,
            is_open=self.is_open,
        )

    def reset_assessment(self):
        """Сбросить закэшированные риск и рекомендацию после изменений."""
        self.__dict__.pop("risk", None)
        self.__dict__.pop("recommendation", None)


class PortalHistory(models.Model):
    portal = models.ForeignKey(
        Portal, on_delete=models.CASCADE,
        related_name="history", verbose_name="Портал",
    )
    changed_at = models.DateTimeField("Когда", auto_now_add=True)
    field_label = models.CharField("Что изменилось", max_length=100)
    old_value = models.CharField("Было", max_length=255, blank=True)
    new_value = models.CharField("Стало", max_length=255, blank=True)
    is_creation = models.BooleanField("Создание портала", default=False)

    class Meta:
        verbose_name = "Запись истории"
        verbose_name_plural = "История изменений"
        ordering = ["-changed_at", "-id"]

    def __str__(self):
        return f"{self.portal.name}: {self.field_label}"


class EventLog(models.Model):
    class Outcome(models.TextChoices):
        SUCCESS = "success", "Выполнено"
        REJECTED = "rejected", "Отклонено"

    portal = models.ForeignKey(
        Portal, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="events", verbose_name="Портал",
    )
    # Название хранится отдельно, чтобы запись не потеряла смысл,
    # даже если портал удалят.
    portal_name = models.CharField("Название портала", max_length=100)
    action = models.CharField("Код действия", max_length=20)
    action_label = models.CharField("Действие", max_length=100)
    outcome = models.CharField("Результат", max_length=10, choices=Outcome.choices)
    message = models.TextField("Что произошло")
    created_at = models.DateTimeField("Когда", auto_now_add=True)

    class Meta:
        verbose_name = "Событие журнала"
        verbose_name_plural = "Журнал событий"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.created_at:%d.%m.%Y %H:%M} {self.portal_name}: {self.action_label}"

    @classmethod
    def record(cls, portal, action, label, outcome, message):
        return cls.objects.create(
            portal=portal, portal_name=portal.name, action=action,
            action_label=label, outcome=outcome, message=message,
        )