from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from . import actions, services
from .models import Portal


class PortalListView(ListView):
    model = Portal
    template_name = "portals/portal_list.html"
    context_object_name = "portals"

    def get_queryset(self):
        portals = list(Portal.objects.all())
        portals.sort(key=lambda p: (not p.is_open, -p.risk.score, p.name))
        return portals

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = build_summary(context["portals"])
        return context


class PortalDetailView(DetailView):
    model = Portal
    template_name = "portals/portal_detail.html"
    context_object_name = "portal"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["history"] = self.object.history.all()
        context["action_states"] = actions.action_states(self.object)
        context["formula"] = {
            "w_stability": services.WEIGHT_STABILITY,
            "w_energy": services.WEIGHT_ENERGY,
            "w_time": services.WEIGHT_TIME,
            "horizon": services.TIME_HORIZON_HOURS,
            "low": services.LOW_LIMIT,
            "critical": services.CRITICAL_LIMIT,
            "urgent": services.URGENT_HOURS,
        }
        return context


class PortalActionView(View):
    """Выполняет действие над порталом (только POST)."""

    http_method_names = ["post"]

    def post(self, request, pk, action):
        if action not in actions.ACTION_LABELS:
            raise Http404("Неизвестное действие")

        confirmed = request.POST.get("confirm") == "1"
        label = actions.ACTION_LABELS[action]

        with transaction.atomic():
            # Блокируем строку, чтобы два клика подряд не наложились.
            portal = get_object_or_404(Portal.objects.select_for_update(), pk=pk)
            try:
                result = actions.execute(portal, action, confirmed=confirmed)
            except actions.ActionNotAllowed as exc:
                level = messages.WARNING if exc.is_warning else messages.ERROR
                messages.add_message(
                    request, level,
                    f"Действие «{label}» не выполнено. {exc.message}",
                )
            else:
                messages.success(request, f"{result.label}. {result.message}")

        return redirect("portals:detail", pk=pk)