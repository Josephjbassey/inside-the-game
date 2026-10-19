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
    path("api/tactical/<int:match_id>/", views.tactical_api, name="tactical_api"),
    path("api/state/<int:match_id>/", views.match_state_api, name="match_state_api"),
    path("api/ask-why/<int:match_id>/", views.ask_why_api, name="ask_why_api"),
]
