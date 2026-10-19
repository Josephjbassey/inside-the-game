from django.urls import path

from . import views

app_name = "matches"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("<int:match_id>/", views.dashboard, name="match_detail"),
    path("<int:match_id>/ticker/", views.ticker_partial, name="ticker_partial"),
    path("<int:match_id>/scoreboard/", views.scoreboard_partial, name="scoreboard_partial"),
    path("<int:match_id>/xg/", views.xg_partial, name="xg_partial"),
    path("studio/<int:match_id>/", views.studio_view, name="studio_view"),
    path("fan/<int:match_id>/", views.fan_view, name="fan_view"),
]
