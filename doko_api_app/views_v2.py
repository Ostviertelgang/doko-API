from django.contrib.auth.models import Group, User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from functools import wraps
import logging

from .models import Player, Game
from .serializers import PlayerSerializer

# Get logger for this module
logger = logging.getLogger('doko_api.views_v2')

# Use AllowAny if authentication is disabled, otherwise use IsAuthenticated
permission_classes_list = [AllowAny] if settings.DISABLE_AUTHENTICATION else [IsAuthenticated]

# Common Swagger parameters
player_uuid_param = openapi.Parameter(
    'player_uuid',
    openapi.IN_PATH,
    description="UUID of the player",
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_UUID,
    required=True
)

def admin_required(view_func):
    """Decorator to check if user is in Admin group"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.groups.filter(name='Admin').exists():
            return view_func(request, *args, **kwargs)
        return Response(
            {'error': 'Admin privileges required'},
            status=status.HTTP_403_FORBIDDEN
        )
    return _wrapped_view

@swagger_auto_schema(
    method='get',
    responses={200: PlayerSerializer}
)
@api_view(['GET'])
@permission_classes(permission_classes_list)
def get_own_profile(request):
    """Get the profile of the currently authenticated user"""
    try:
        player = request.user.player
        serializer = PlayerSerializer(player)
        return Response(serializer.data)
    except Player.DoesNotExist:
        return Response(
            {'error': 'Player profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@swagger_auto_schema(
    method='patch',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: PlayerSerializer}
)
@api_view(['PATCH'])
@permission_classes(permission_classes_list)
def update_own_profile(request):
    """Update the profile of the currently authenticated user"""
    try:
        player = request.user.player
        serializer = PlayerSerializer(player, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Player.DoesNotExist:
        return Response(
            {'error': 'Player profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )

# Admin endpoints
@swagger_auto_schema(
    method='get',
    responses={200: PlayerSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes(permission_classes_list)
@admin_required
def list_players(request):
    """List all players (Admin only)"""
    players = Player.objects.filter(flag_removed=False)
    serializer = PlayerSerializer(players, many=True)
    return Response(serializer.data)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['name'],
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER)
        }
    ),
    responses={201: PlayerSerializer}
)
@api_view(['POST'])
@permission_classes(permission_classes_list)
@admin_required
def create_player(request):
    """Create a new player (Admin only)"""
    serializer = PlayerSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='delete',
    manual_parameters=[player_uuid_param],
    responses={204: 'No content'}
)
@api_view(['DELETE'])
@permission_classes(permission_classes_list)
@admin_required
def delete_player(request, player_uuid):
    """Soft delete a player (Admin only)"""
    try:
        player = Player.objects.get(player_id=player_uuid)
        player.flag_removed = True
        player.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Player.DoesNotExist:
        return Response(
            {'error': 'Player not found'},
            status=status.HTTP_404_NOT_FOUND
        )