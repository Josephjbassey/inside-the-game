from django.urls import path

from . import views

app_name = "narratives"

urlpatterns = [
    path(
        "api/narrative/<int:match_id>/",
        views.narrative_api,
        name="narrative_api",
    ),
    path("api/recap/<int:match_id>/", views.recap_api, name="recap_api"),
]
