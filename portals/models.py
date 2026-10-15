from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Portal(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        CLOSED = "closed", "Закрыт"

    name = models.CharField(
        "Название портала",
        max_length=100,
        unique=True,
    )
    destination_world = models.CharField(
        "Мир назначения",
        max_length=100,
    )
    energy_level = models.PositiveSmallIntegerField(
        "Уровень энергии",
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="От 0 до 100",
    )
    stability = models.PositiveSmallIntegerField(
        "Стабильность",
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="От 0 (схлопнется) до 100 (полностью стабилен)",
    )
    creatures_count = models.PositiveIntegerField(
        "Количество существ внутри",
        default=0,
    )
    status = models.CharField(
        "Статус",
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Портал"
        verbose_name_plural = "Порталы"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} → {self.destination_world}"