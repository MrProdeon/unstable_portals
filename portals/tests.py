from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import actions
from .models import Portal, EventLog


def make_portal(**kwargs):
    data = dict(
        name="Тест", destination_world="Мир", energy_level=50, stability=60,
        creatures_count=0, status="open",
        collapse_at=timezone.now() + timedelta(hours=30),
    )
    data.update(kwargs)
    return Portal.objects.create(**data)


class ForbiddenActionsTests(TestCase):
    def test_cannot_stabilize_closed_portal(self):
        portal = make_portal(status="closed")
        with self.assertRaises(actions.ActionNotAllowed):
            actions.execute(portal, "stabilize")

    def test_cannot_send_observer_to_critical_portal(self):
        portal = make_portal(stability=10, energy_level=90,
                             collapse_at=timezone.now() + timedelta(hours=4))
        self.assertEqual(portal.risk.level, "critical")
        with self.assertRaises(actions.ActionNotAllowed):
            actions.execute(portal, "observer")

    def test_close_with_creatures_requires_confirmation(self):
        portal = make_portal(creatures_count=5)
        with self.assertRaises(actions.ActionNotAllowed) as ctx:
            actions.execute(portal, "close")
        self.assertTrue(ctx.exception.is_warning)
        portal.refresh_from_db()
        self.assertEqual(portal.status, "open")

        actions.execute(portal, "close", confirmed=True)
        portal.refresh_from_db()
        self.assertEqual(portal.status, "closed")

    def test_cannot_mark_twice(self):
        portal = make_portal()
        actions.execute(portal, "question")
        with self.assertRaises(actions.ActionNotAllowed):
            actions.execute(portal, "question")


class StabilizeTests(TestCase):
    def test_stabilize_lowers_risk(self):
        portal = make_portal(stability=15, energy_level=80,
                             collapse_at=timezone.now() + timedelta(hours=48))
        result = actions.execute(portal, "stabilize")
        self.assertLess(result.risk_after, result.risk_before)
        self.assertEqual(portal.stability, 40)

    def test_forbidden_action_via_http_does_not_change_portal(self):
        portal = make_portal(status="closed")
        self.client.post(reverse("portals:action", args=[portal.pk, "stabilize"]))
        portal.refresh_from_db()
        self.assertEqual(portal.stability, 60)

class EventLogTests(TestCase):
    def test_log_after_several_operations(self):
        portal = make_portal(stability=15, energy_level=80, creatures_count=2,
                             collapse_at=timezone.now() + timedelta(hours=48))
        url = lambda code: reverse("portals:action", args=[portal.pk, code])

        self.client.post(url("stabilize"))   # выполнено
        self.client.post(url("question"))    # выполнено
        self.client.post(url("question"))    # отклонено (уже помечен)
        self.client.post(url("close"))       # отклонено (нет подтверждения)
        self.client.post(url("close"), {"confirm": "1"})   # выполнено
        self.client.post(url("stabilize"))   # отклонено (закрыт)

        outcomes = list(EventLog.objects.order_by("id")
                        .values_list("outcome", flat=True))
        self.assertEqual(outcomes, ["success", "success", "rejected",
                                    "rejected", "success", "rejected"])