from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from portals.models import Portal

DEMO = [
    # название, мир, энергия, стабильность, существ, статус, часов до схлопывания
    ("Врата Зари", "Элизиум", 20, 95, 0, "open", None),                 # низкий
    ("Багровая трещина", "Пепельный мир", 90, 25, 14, "open", 4),       # критический, срочно
    ("Нестабильный разлом", "Бездна", 80, 15, 5, "open", 48),           # критический, есть время
    ("Зеркальный проход", "Мир отражений", 55, 60, 3, "open", 30),      # средний, есть существа
    ("Тихая арка", "Сумеречный лес", 40, 70, 0, "open", 20),            # средний, без существ
    ("Старый колодец", "Подземье", 70, 10, 2, "closed", None),          # закрыт
]


class Command(BaseCommand):
    help = "Создаёт демонстрационные порталы (--clear удаляет все порталы)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Удалить все порталы (для проверки пустого списка)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Portal.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Удалено записей: {deleted}"))
            return

        now = timezone.now()
        for name, world, energy, stab, creatures, status, hours in DEMO:
            Portal.objects.update_or_create(
                name=name,
                defaults={
                    "destination_world": world,
                    "energy_level": energy,
                    "stability": stab,
                    "creatures_count": creatures,
                    "status": status,
                    "under_question": False,
                    "collapse_at": now + timedelta(hours=hours) if hours else None,
                },
            )
        self.stdout.write(self.style.SUCCESS("Демо-порталы созданы"))