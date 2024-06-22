"""
URL configuration for doko_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include, re_path
from rest_framework import routers, permissions
from django.contrib import admin
from doko_api_app import views

from doko_api_app import views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
# import settings
from django.conf import settings

schema_view = get_schema_view(
   openapi.Info(
      title="doko-API",
      default_version='v1',
      description="API documentation for Doko API",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   url=settings.SWAGGER_SETTINGS.get('API_URL')
)

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'games', views.GameViewSet)
router.register(r'rounds', views.RoundViewSet)
router.register(r'player_points', views.PlayerPointsViewSet)
router.register(r'players', views.PlayerViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('games/<uuid:game_id>/add_player_points/', views.add_player_points_to_game, name='add_player_points_to_game'),
    path('games/<uuid:game_id>/commit_game/', views.commit_game, name='commit_game'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path("admin/", admin.site.urls),
    path('get_export/', views.make_csv_export, name='get_export'),
    path('import_csv/', views.import_csv, name='import_csv'),
    path('games/<uuid:game_id>/rounds/', views.get_all_rounds, name='get_all_rounds'),
    path('games/<uuid:game_id>/add_round/', views.add_round, name='add_round'),
    path('games/<uuid:game_id>/get_pflichtsolo/', views.get_players_with_pflichtsolo, name='get_pflichtsolo'),
    path('stats/<uuid:player_id>/game_points/', views.get_player_points_for_game_stats),
    path('stats/<uuid:player_id>/round_points/', views.get_player_points_for_round_stats),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('games/<uuid:game_id>/undo_round/', views.undo_round, name='undo_round'),
    path('games/<uuid:game_id>/get_bock_status/', views.get_bock_status, name='get_bock_status'),
]
