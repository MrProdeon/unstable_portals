from django.urls import path

from . import views

app_name = "portals"

urlpatterns = [
    path("", views.PortalListView.as_view(), name="list"),
    path("portals/<int:pk>/", views.PortalDetailView.as_view(), name="detail"),
    path("portals/<int:pk>/actions/<slug:action>/",
         views.PortalActionView.as_view(), name="action"),
]