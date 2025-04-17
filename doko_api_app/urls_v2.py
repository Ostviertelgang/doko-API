from django.urls import path
from . import views_v2

urlpatterns = [
    # Profile endpoints (available to all authenticated users)
    path('profile/', views_v2.get_own_profile, name='v2-profile-get'),
    path('profile/update/', views_v2.update_own_profile, name='v2-profile-update'),

    # Admin endpoints
    path('admin/players/', views_v2.list_players, name='v2-admin-players-list'),
    path('admin/players/create/', views_v2.create_player, name='v2-admin-player-create'),
    path('admin/players/<uuid:player_uuid>/delete/', 
         views_v2.delete_player, 
         name='v2-admin-player-delete'),
]