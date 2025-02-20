"""
URL configuration for doko_api project.
"""
from django.urls import path, include, re_path
from rest_framework import routers, permissions
from django.contrib import admin
from doko_api_app import views
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from doko_api_app import views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from doko_api_app.views import GenerateAuthToken

# Create unified schema view
schema_view = get_schema_view(
   openapi.Info(
      title="Doko API",
      default_version='v2',
      description="""
      Doko Game API Documentation
      
      This API provides endpoints for managing Doko card games, players, and statistics.
      
      ## Versioning
      
      The API supports two versions:
      - **v1**: Original endpoints for game management
      - **v2**: Enhanced statistics and analytics endpoints
      
      All v2 endpoints are prefixed with `/v2/`
      
      ## Authentication
      
      All endpoints require JWT authentication. Include the token in the Authorization header:
      ```
      Authorization: Bearer <your-token>
      ```
      
      ## Error Responses
      
      The API uses standard HTTP status codes:
      - 200: Success
      - 201: Created
      - 400: Bad Request
      - 401: Unauthorized
      - 404: Not Found
      - 500: Server Error
      
      Error responses include a message explaining the error.
      """,
      contact=openapi.Contact(email="todo@todo.com"),
      license=openapi.License(name="todo License"),
   ),
   public=True,
   patterns=[
       path('', include('doko_api_app.urls_v1')),
       path('v2/', include('doko_api_app.urls_v2')),
   ],
)

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'games', views.GameViewSet)
router.register(r'rounds', views.RoundViewSet)
router.register(r'player_points', views.PlayerPointsViewSet)
router.register(r'players', views.PlayerViewSet)

urlpatterns = [
    # Include v1 URLs at root level
    path('', include('doko_api_app.urls_v1')),
    
    # Include v2 URLs under /v2/ prefix
    path('v2/', include('doko_api_app.urls_v2')),
    
    # Admin and authentication
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path("admin/", admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/generate-token/', GenerateAuthToken.as_view(), name='generate_token'),
    
    # OpenAPI/Swagger documentation (unified v1 + v2)
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
