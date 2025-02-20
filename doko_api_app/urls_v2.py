from django.urls import path
from . import views_v2

urlpatterns = [
    # Player summary stats
    path('players/<uuid:player_uuid>/summary-stats/',
         views_v2.get_player_summary_stats,
         name='v2-player-summary-stats'),
         
    # Game type stats
    path('players/<uuid:player_uuid>/game-type-stats/',
         views_v2.get_game_type_stats,
         name='v2-game-type-stats'),
         
    # Game points
    path('players/<uuid:player_uuid>/game-points/',
         views_v2.get_game_points,
         name='v2-game-points'),
         
    # Round points
    path('players/<uuid:player_uuid>/round-points/',
         views_v2.get_round_points,
         name='v2-round-points'),
]