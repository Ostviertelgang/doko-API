from django.urls import path
from . import stats_views

urlpatterns = [
    # Best Round Analytics
    path('player/<uuid:player_id>/best-rounds/', 
         stats_views.get_player_best_rounds, 
         name='stats-player-best-rounds'),
    
    # Player Leaderboard
    path('leaderboard/', 
         stats_views.get_leaderboard, 
         name='stats-leaderboard'),
    
    # Win/Loss Analysis
    path('player/<uuid:player_id>/win-loss/', 
         stats_views.get_player_win_loss, 
         name='stats-player-win-loss'),
    
    # Game Type Performance
    path('player/<uuid:player_id>/game-type-performance/', 
         stats_views.get_game_type_performance, 
         name='stats-player-game-type-performance'),
    
    # Performance Trend
    path('player/<uuid:player_id>/trends/', 
         stats_views.get_player_trends, 
         name='stats-player-trends'),
]