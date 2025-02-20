from django.db.models import Avg, Count, Sum, Max, Min, F, Q, FloatField, IntegerField
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from rest_framework.response import Response
from django.db.models.functions import Coalesce
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
import logging

from .models import Player, Game, Round, PlayerPoints
from .serializers import PlayerSerializer, GameSerializer, PlayerPointsSerializer

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

date_params = [
    openapi.Parameter(
        'start_date',
        openapi.IN_QUERY,
        description="Filter points after this date (YYYY-MM-DD)",
        type=openapi.TYPE_STRING,
        format=openapi.FORMAT_DATE
    ),
    openapi.Parameter(
        'end_date',
        openapi.IN_QUERY,
        description="Filter points before this date (YYYY-MM-DD)",
        type=openapi.TYPE_STRING,
        format=openapi.FORMAT_DATE
    )
]

sort_params = [
    openapi.Parameter(
        'sort_by',
        openapi.IN_QUERY,
        description="Sort field (points, date)",
        type=openapi.TYPE_STRING,
        enum=['points', 'date']
    ),
    openapi.Parameter(
        'sort_order',
        openapi.IN_QUERY,
        description="Sort order (asc, desc)",
        type=openapi.TYPE_STRING,
        enum=['asc', 'desc']
    )
]

# Swagger schemas
summary_stats_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'total_games': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of games played'),
        'total_rounds': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of rounds played'),
        'total_points': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total points earned'),
        'average_points_per_game': openapi.Schema(type=openapi.TYPE_NUMBER, description='Average points per game'),
        'average_points_per_round': openapi.Schema(type=openapi.TYPE_NUMBER, description='Average points per round'),
        'highest_game_points': openapi.Schema(type=openapi.TYPE_INTEGER, description='Highest points in a single game'),
        'lowest_game_points': openapi.Schema(type=openapi.TYPE_INTEGER, description='Lowest points in a single game'),
        'win_rate': openapi.Schema(type=openapi.TYPE_NUMBER, description='Win rate percentage'),
        'solo_games': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of solo games played'),
        'solo_win_rate': openapi.Schema(type=openapi.TYPE_NUMBER, description='Win rate percentage in solo games'),
        'average_position': openapi.Schema(type=openapi.TYPE_NUMBER, description='Average finishing position'),
        'first_place_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of first place finishes'),
        'last_place_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of last place finishes')
    }
)

game_type_stats_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'normal_games': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'win_rate': openapi.Schema(type=openapi.TYPE_NUMBER),
                'average_points': openapi.Schema(type=openapi.TYPE_NUMBER),
                'total_points': openapi.Schema(type=openapi.TYPE_INTEGER),
                'average_position': openapi.Schema(type=openapi.TYPE_NUMBER)
            }
        ),
        'solo_games': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'win_rate': openapi.Schema(type=openapi.TYPE_NUMBER),
                'average_points': openapi.Schema(type=openapi.TYPE_NUMBER),
                'total_points': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        'pflichtsolo_games': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'win_rate': openapi.Schema(type=openapi.TYPE_NUMBER),
                'average_points': openapi.Schema(type=openapi.TYPE_NUMBER),
                'total_points': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        'bock_rounds': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'win_rate': openapi.Schema(type=openapi.TYPE_NUMBER),
                'average_points': openapi.Schema(type=openapi.TYPE_NUMBER),
                'total_points': openapi.Schema(type=openapi.TYPE_INTEGER),
                'average_multiplier': openapi.Schema(type=openapi.TYPE_NUMBER)
            }
        )
    }
)

@swagger_auto_schema(
    method='get',
    manual_parameters=[player_uuid_param],
    responses={
        200: openapi.Response('Successful response', summary_stats_schema),
        404: 'Player not found'
    }
)
@api_view(['GET'])
@permission_classes(permission_classes_list)
def get_player_summary_stats(request, player_uuid):
    """Get aggregated statistics for a player"""
    try:
        player = Player.objects.get(player_id=player_uuid)
    except Player.DoesNotExist:
        return Response({'error': 'Player not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get all games where player has points
    games = Game.objects.filter(
        player_points__player=player,
        flag_removed=False
    ).distinct()

    # Get all rounds where player has points
    rounds = Round.objects.filter(
        player_points__player=player
    ).distinct()

    # Calculate stats
    game_points = PlayerPoints.objects.filter(
        player=player,
        games__isnull=False,
        games__flag_removed=False
    )

    stats = {
        'total_games': games.count(),
        'total_rounds': rounds.count(),
        'total_points': game_points.aggregate(
            total=Coalesce(Sum('points', output_field=IntegerField()), 0)
        )['total'],
        'average_points_per_game': game_points.aggregate(
            avg=Coalesce(Avg('points', output_field=FloatField()), 0.0)
        )['avg'],
        'average_points_per_round': PlayerPoints.objects.filter(
            player=player,
            rounds__isnull=False
        ).aggregate(
            avg=Coalesce(Avg('points', output_field=FloatField()), 0.0)
        )['avg'],
        'highest_game_points': game_points.aggregate(
            max=Coalesce(Max('points', output_field=IntegerField()), 0)
        )['max'],
        'lowest_game_points': game_points.aggregate(
            min=Coalesce(Min('points', output_field=IntegerField()), 0)
        )['min'],
        'win_rate': rounds.filter(
            player_points__player=player,
            player_points__points__gt=0
        ).count() / max(rounds.count(), 1) * 100,
        'solo_games': rounds.filter(
            was_solo_by=player
        ).count(),
        'solo_win_rate': rounds.filter(
            was_solo_by=player,
            player_points__player=player,
            player_points__points__gt=0
        ).count() / max(rounds.filter(was_solo_by=player).count(), 1) * 100,
        'average_position': 0,  # TODO: Implement position calculation
        'first_place_count': 0,  # TODO: Implement position counting
        'last_place_count': 0  # TODO: Implement position counting
    }

    return Response(stats)

@swagger_auto_schema(
    method='get',
    manual_parameters=[player_uuid_param],
    responses={
        200: openapi.Response('Successful response', game_type_stats_schema),
        404: 'Player not found'
    }
)
@api_view(['GET'])
@permission_classes(permission_classes_list)
def get_game_type_stats(request, player_uuid):
    """Get statistics broken down by game type"""
    try:
        player = Player.objects.get(player_id=player_uuid)
    except Player.DoesNotExist:
        return Response({'error': 'Player not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get all rounds for the player
    rounds = Round.objects.filter(
        player_points__player=player
    ).distinct()

    # Normal games (no solo and no pflichtsolo)
    normal_rounds = rounds.filter(
        was_solo_by__isnull=True,
        was_pflichtsolo_by__isnull=True
    )
    normal_stats = {
        'count': normal_rounds.count(),
        'win_rate': round(normal_rounds.filter(
            player_points__player=player,
            player_points__points__gt=0
        ).count() / max(normal_rounds.count(), 1) * 100, 2),
        'average_points': PlayerPoints.objects.filter(
            player=player,
            rounds__in=normal_rounds
        ).aggregate(
            avg=Coalesce(Avg('points', output_field=FloatField()), 0.0)
        )['avg'],
        'total_points': PlayerPoints.objects.filter(
            player=player,
            rounds__in=normal_rounds
        ).aggregate(
            total=Coalesce(Sum('points', output_field=IntegerField()), 0)
        )['total'],
        'average_position': 0  # TODO: Implement position calculation
    }

    # Solo games
    solo_rounds = rounds.filter(was_solo_by=player)
    solo_stats = {
        'count': solo_rounds.count(),
        'win_rate': round(solo_rounds.filter(
            player_points__player=player,
            player_points__points__gt=0
        ).count() / max(solo_rounds.count(), 1) * 100, 2),
        'average_points': PlayerPoints.objects.filter(
            player=player,
            rounds__in=solo_rounds
        ).aggregate(
            avg=Coalesce(Avg('points', output_field=FloatField()), 0.0)
        )['avg'],
        'total_points': PlayerPoints.objects.filter(
            player=player,
            rounds__in=solo_rounds
        ).aggregate(
            total=Coalesce(Sum('points', output_field=IntegerField()), 0)
        )['total']
    }

    # Pflichtsolo games
    pflichtsolo_rounds = rounds.filter(was_pflichtsolo_by=player)
    pflichtsolo_stats = {
        'count': pflichtsolo_rounds.count(),
        'win_rate': round(pflichtsolo_rounds.filter(
            player_points__player=player,
            player_points__points__gt=0
        ).count() / max(pflichtsolo_rounds.count(), 1) * 100, 2),
        'average_points': PlayerPoints.objects.filter(
            player=player,
            rounds__in=pflichtsolo_rounds
        ).aggregate(
            avg=Coalesce(Avg('points', output_field=FloatField()), 0.0)
        )['avg'],
        'total_points': PlayerPoints.objects.filter(
            player=player,
            rounds__in=pflichtsolo_rounds
        ).aggregate(
            total=Coalesce(Sum('points', output_field=IntegerField()), 0)
        )['total']
    }

    # Bock rounds
    bock_rounds = rounds.filter(bocks_parallel__gt=0)
    bock_stats = {
        'count': bock_rounds.count(),
        'win_rate': round(bock_rounds.filter(
            player_points__player=player,
            player_points__points__gt=0
        ).count() / max(bock_rounds.count(), 1) * 100, 2),
        'average_points': PlayerPoints.objects.filter(
            player=player,
            rounds__in=bock_rounds
        ).aggregate(
            avg=Coalesce(Avg('points', output_field=FloatField()), 0.0)
        )['avg'],
        'total_points': PlayerPoints.objects.filter(
            player=player,
            rounds__in=bock_rounds
        ).aggregate(
            total=Coalesce(Sum('points', output_field=IntegerField()), 0)
        )['total'],
        'average_multiplier': bock_rounds.aggregate(
            avg=Coalesce(Avg('bock_multiplier', output_field=FloatField()), 0.0)
        )['avg']
    }

    return Response({
        'normal_games': normal_stats,
        'solo_games': solo_stats,
        'pflichtsolo_games': pflichtsolo_stats,
        'bock_rounds': bock_stats
    })

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        player_uuid_param,
        *date_params,
        openapi.Parameter(
            'is_game_closed',
            openapi.IN_QUERY,
            description="Filter by game status",
            type=openapi.TYPE_BOOLEAN
        ),
        *sort_params
    ],
    responses={
        200: openapi.Response('Successful response'),
        404: 'Player not found'
    }
)
@api_view(['GET'])
@permission_classes(permission_classes_list)
def get_game_points(request, player_uuid):
    """Get game-level points for a player"""
    logger.debug(f"Getting game points for player {player_uuid}")
    
    try:
        player = Player.objects.get(player_id=player_uuid)
        logger.debug(f"Found player: {player.name}")
    except Player.DoesNotExist:
        logger.warning(f"Player {player_uuid} not found")
        return Response({'error': 'Player not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get query parameters
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    is_game_closed = request.query_params.get('is_game_closed')
    sort_by = request.query_params.get('sort_by', 'date')
    sort_order = request.query_params.get('sort_order', 'desc')
    logger.debug(f"Query params: start_date={start_date}, end_date={end_date}, is_game_closed={is_game_closed}, sort_by={sort_by}, sort_order={sort_order}")

    # Get all game points for the player
    points = PlayerPoints.objects.filter(
        player=player,
        games__isnull=False,
        games__flag_removed=False
    ).select_related('player').prefetch_related('games')
    logger.debug(f"Found {points.count()} game points")

    # Apply filters
    if start_date:
        points = points.filter(games__created_at__gte=start_date)
    if end_date:
        points = points.filter(games__created_at__lte=end_date)
    if is_game_closed is not None:
        is_closed = is_game_closed.lower() == 'true'
        points = points.filter(games__is_closed=is_closed)

    # Prepare sorting
    if sort_by == 'date':
        sort_field = 'games__created_at'
    else:
        sort_field = 'points'
    if sort_order == 'desc':
        sort_field = f'-{sort_field}'
    points = points.order_by(sort_field)

    # Prepare response data
    points_data = []
    for point in points:
        logger.debug(f"Processing point {point.id} with points={point.points}")
        games = list(point.games.all())  # Convert to list to evaluate query
        logger.debug(f"Found {len(games)} games for this point")
        logger.debug(f"Games: {games}")
        
        if games:
            game = games[0]  # Take the first game
            logger.debug(f"Processing game {game.game_id} ({game.game_name})")
            
            # Get solo count for this player in this game
            solo_count = Round.objects.filter(
                game=game,
                was_solo_by=player
            ).count()
            logger.debug(f"Found {solo_count} solo rounds for player in this game")

            total_rounds = Round.objects.filter(game=game).count()
            logger.debug(f"Total rounds in game: {total_rounds}")

            points_data.append({
                'game_id': game.game_id,
                'game_name': game.game_name,
                'points': point.points,
                'created_at': game.created_at,
                'closed_at': game.closed_at,
                'total_rounds': total_rounds,
                'final_position': 0,  # TODO: Implement position calculation
                'solo_count': solo_count
            })

    # Calculate aggregates
    aggregates = {
        'total_points': sum(p['points'] for p in points_data),
        'average_points': sum(p['points'] for p in points_data) / len(points_data) if points_data else 0,
        'min_points': min((p['points'] for p in points_data), default=0),
        'max_points': max((p['points'] for p in points_data), default=0),
        'total_games': len(points_data)
    }

    return Response({
        'total_count': len(points_data),
        'points': points_data,
        'aggregates': aggregates
    })

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        player_uuid_param,
        *date_params,
        openapi.Parameter(
            'game_id',
            openapi.IN_QUERY,
            description="Filter by game ID",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID
        ),
        openapi.Parameter(
            'game_type',
            openapi.IN_QUERY,
            description="Filter by game type (normal, solo, pflichtsolo)",
            type=openapi.TYPE_STRING,
            enum=['normal', 'solo', 'pflichtsolo']
        ),
        *sort_params
    ],
    responses={
        200: openapi.Response('Successful response'),
        404: 'Player not found'
    }
)
@api_view(['GET'])
@permission_classes(permission_classes_list)
def get_round_points(request, player_uuid):
    """Get round-level points for a player"""
    try:
        player = Player.objects.get(player_id=player_uuid)
    except Player.DoesNotExist:
        return Response({'error': 'Player not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get query parameters
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    game_id = request.query_params.get('game_id')
    game_type = request.query_params.get('game_type')
    sort_by = request.query_params.get('sort_by', 'date')
    sort_order = request.query_params.get('sort_order', 'desc')

    # Get all round points for the player
    points = PlayerPoints.objects.filter(
        player=player,
        rounds__isnull=False
    ).select_related('player').prefetch_related('rounds__game')

    # Apply filters
    if start_date:
        points = points.filter(rounds__game__created_at__gte=start_date)
    if end_date:
        points = points.filter(rounds__game__created_at__lte=end_date)
    if game_id:
        points = points.filter(rounds__game__game_id=game_id)

    # Apply game type filter
    if game_type:
        if game_type == 'solo':
            points = points.filter(rounds__was_solo_by=player)
        elif game_type == 'pflichtsolo':
            points = points.filter(rounds__was_pflichtsolo_by=player)
        elif game_type == 'normal':
            points = points.filter(
                rounds__was_solo_by__isnull=True,
                rounds__was_pflichtsolo_by__isnull=True
            )

    # Prepare sorting
    if sort_by == 'date':
        sort_field = 'rounds__game__created_at'
    else:
        sort_field = 'points'
    if sort_order == 'desc':
        sort_field = f'-{sort_field}'
    points = points.order_by(sort_field)

    # Prepare response data
    points_data = []
    for point in points:
        round_obj = point.rounds.first()  # Get the associated round
        if round_obj:
            game = round_obj.game
            points_data.append({
                'round_id': round_obj.id,
                'game_id': game.game_id,
                'points': point.points,
                'was_solo': round_obj.was_solo_by == player,
                'was_pflichtsolo': round_obj.was_pflichtsolo_by == player,
                'bock_multiplier': round_obj.bock_multiplier,
                'created_at': game.created_at
            })

    # Calculate aggregates
    aggregates = {
        'total_points': sum(p['points'] for p in points_data),
        'average_points': sum(p['points'] for p in points_data) / len(points_data) if points_data else 0,
        'min_points': min((p['points'] for p in points_data), default=0),
        'max_points': max((p['points'] for p in points_data), default=0),
        'total_rounds': len(points_data)
    }

    return Response({
        'total_count': len(points_data),
        'points': points_data,
        'aggregates': aggregates
    })