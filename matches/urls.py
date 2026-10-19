from django.urls import path

from . import views

app_name = "matches"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("<int:match_id>/", views.dashboard, name="match_detail"),
    path("<int:match_id>/ticker/", views.ticker_partial, name="ticker_partial"),
    path("<int:match_id>/scoreboard/", views.scoreboard_partial, name="scoreboard_partial"),
    path("<int:match_id>/xg/", views.xg_partial, name="xg_partial"),
    path("<int:match_id>/stats/", views.match_stats_api, name="match_stats_api"),
    path("<int:match_id>/turning-points/", views.turning_points_api, name="turning_points_api"),
    path("<int:match_id>/tactical/", views.tactical_view, name="tactical_view"),
    path("<int:match_id>/ask-why/", views.ask_why_view, name="ask_why_view"),
    path("studio/<int:match_id>/", views.studio_view, name="studio_view"),
    path("fan/<int:match_id>/", views.fan_view, name="fan_view"),
]
