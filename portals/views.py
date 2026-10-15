from django.views.generic import DetailView, ListView

from . import services
from .models import Portal


class PortalListView(ListView):
    model = Portal
    template_name = "portals/portal_list.html"
    context_object_name = "portals"

    def get_queryset(self):
        # Сначала открытые порталы, внутри — по убыванию риска.
        portals = list(Portal.objects.all())
        portals.sort(key=lambda p: (not p.is_open, -p.risk.score, p.name))
        return portals


class PortalDetailView(DetailView):
    model = Portal
    template_name = "portals/portal_detail.html"
    context_object_name = "portal"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["history"] = self.object.history.all()
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