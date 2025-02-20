from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'games', views.GameViewSet)
router.register(r'rounds', views.RoundViewSet)
router.register(r'player_points', views.PlayerPointsViewSet)
router.register(r'players', views.PlayerViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('games/<uuid:game_id>/add_player_points/', views.add_player_points_to_game, name='add_player_points_to_game'),
    path('games/<uuid:game_id>/commit_game/', views.commit_game, name='commit_game'),
    path('get_export/', views.make_csv_export, name='get_export'),
    path('import_csv/', views.import_csv, name='import_csv'),
    path('games/<uuid:game_id>/rounds/', views.get_all_rounds, name='get_all_rounds'),
    path('games/<uuid:game_id>/add_round/', views.add_round, name='add_round'),
    path('games/<uuid:game_id>/get_pflichtsolo/', views.get_players_with_pflichtsolo, name='get_pflichtsolo'),
    path('stats/<uuid:player_id>/game_points/', views.get_player_points_for_game_stats),
    path('stats/<uuid:player_id>/round_points/', views.get_player_points_for_round_stats),
    path('games/<uuid:game_id>/undo_round/', views.undo_round, name='undo_round'),
    path('games/<uuid:game_id>/get_bock_status/', views.get_bock_status, name='get_bock_status'),
    path('games/<uuid:game_id>/points-progression-gif/', views.get_points_progression_gif, name='points-progression-gif'),
    path('games/<uuid:game_id>/points-progression-image/', views.get_points_progression_image, name='points-progression-image'),
]