from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'games', views.GameViewSet)
router.register(r'rounds', views.RoundViewSet)
router.register(r'players', views.PlayerViewSet)
router.register(r'player_points', views.PlayerPointsViewSet)

# V1 API endpoints for backward compatibility
urlpatterns = [
    path('', include(router.urls)),
    # Game management endpoints
    path('games/<uuid:game_id>/commit_game/', views.commit_game, name='commit_game'),
    path('games/<uuid:game_id>/add_round/', views.add_round, name='add_round'),
    path('games/<uuid:game_id>/get_bock_status/', views.get_bock_status, name='get_bock_status'),
    path('games/<uuid:game_id>/undo_round/', views.undo_round, name='undo_round'),
    path('games/<uuid:game_id>/add_player_points/', views.add_player_points_to_game, name='add_player_points_to_game'),
    path('games/<uuid:game_id>/get_players_with_pflichtsolo/', views.get_players_with_pflichtsolo, name='get_players_with_pflichtsolo'),
    path('games/<uuid:game_id>/get_all_rounds/', views.get_all_rounds, name='get_all_rounds'),
    path('games/<uuid:game_id>/rounds/', views.get_all_rounds, name='game_rounds'),
    path('games/<uuid:game_id>/points_progression.gif', views.get_points_progression_gif, name='get_points_progression_gif'),
    path('games/<uuid:game_id>/points_progression.png', views.get_points_progression_image, name='get_points_progression_image'),
    path('games/<uuid:game_id>/points-progression-gif/', views.get_points_progression_gif, name='get_points_progression_gif_alt'),
    path('games/<uuid:game_id>/points-progression-image/', views.get_points_progression_image, name='get_points_progression_image_alt'),
    
    # Player stats endpoints
    path('players/<uuid:player_id>/get_player_points_for_game_stats/', views.get_player_points_for_game_stats, name='get_player_points_for_game_stats'),
    path('players/<uuid:player_id>/get_player_points_for_round_stats/', views.get_player_points_for_round_stats, name='get_player_points_for_round_stats'),
    
    path('stats/<uuid:player_id>/game_points/', views.get_player_points_for_game_stats, name='player_game_points'),
    
    # Import/Export endpoints
    path('make_csv_export/', views.make_csv_export, name='make_csv_export'),
    path('import_csv/', views.import_csv, name='import_csv'),
]