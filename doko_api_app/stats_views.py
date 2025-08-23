from django.db.models import Sum, Avg, Count, Case, When, F, Q, Value, FloatField
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import datetime, timedelta

from .models import Game, Round, PlayerPoints, Player
from .stats_serializers import (
    BestRoundSerializer, 
    PlayerLeaderboardEntrySerializer,
    WinLossStatsSerializer,
    GameTypePerformanceSerializer,
    TrendAnalysisSerializer
)

@api_view(['GET'])
def get_player_best_rounds(request, player_id):
    """
    Get a player's best rounds based on points or other metrics
    
    Query Parameters:
    - metric: What to sort by (points, win_margin) - default "points"
    - limit: Number of rounds to return (default 5)
    - game_type: Filter by game type (normal, solo, pflichtsolo)
    """
    try:
        # Validate player exists
        player = Player.objects.get(player_id=player_id)
    except Player.DoesNotExist:
        return Response({'error': 'Player not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    # Parse query parameters
    metric = request.GET.get('metric', 'points')
    try:
        limit = int(request.GET.get('limit', 5))
        if limit < 1:
            return Response(
                {'error': 'Limit must be a positive number'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except ValueError:
        return Response(
            {'error': 'Invalid limit parameter'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    game_type = request.GET.get('game_type', None)
    
    # Build the query
    # First, get player points that are associated with rounds
    player_points = PlayerPoints.objects.filter(
        player=player,
        rounds__isnull=False
    )
    
    # Get the rounds associated with these player points
    rounds_query = Round.objects.filter(
        player_points__in=player_points
    ).distinct()
    
    # Filter by game type if requested
    if game_type:
        if game_type == 'solo':
            rounds_query = rounds_query.filter(was_solo_by=player)
        elif game_type == 'pflichtsolo':
            rounds_query = rounds_query.filter(was_pflichtsolo_by=player)
        elif game_type == 'normal':
            rounds_query = rounds_query.filter(
                ~Q(was_solo_by=player) & ~Q(was_pflichtsolo_by=player)
            )
    
    # Order by the requested metric
    if metric == 'points':
        # We need to annotate with the specific player's points
        # This is a bit complex since we need to join back to PlayerPoints
        # Get the player's points for each round
        player_points_subquery = PlayerPoints.objects.filter(
            player=player,
            rounds=F('id')  # This creates a correlation to the outer query
        ).values('points')[:1]
        
        rounds_query = rounds_query.annotate(
            player_score=Coalesce(player_points_subquery, Value(0))
        ).order_by('-player_score', '-created_at')
    
    # Get top N rounds
    best_rounds = rounds_query[:limit]
    
    # Serialize the results
    serializer = BestRoundSerializer(
        best_rounds, 
        many=True,
        context={'player_id': str(player_id)}
    )
    
    return Response({'best_rounds': serializer.data})

@api_view(['GET'])
def get_leaderboard(request):
    """
    Get player leaderboard based on various metrics
    
    Query Parameters:
    - metric: Ranking criteria (total_points, win_rate, avg_points_per_game)
    - timeframe: Time period (all, month, year)
    - limit: Number of players to show
    """
    # Parse query parameters
    metric = request.GET.get('metric', 'total_points')
    timeframe = request.GET.get('timeframe', 'all')
    
    try:
        limit = int(request.GET.get('limit', 10))
        if limit < 1:
            return Response(
                {'error': 'Limit must be a positive number'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except ValueError:
        return Response(
            {'error': 'Invalid limit parameter'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Start with all players that aren't marked as removed
    players_query = Player.objects.filter(flag_removed=False)
    
    # Set up timeframe filter
    timeframe_filter = {}
    now = datetime.now()
    
    if timeframe == 'month':
        start_date = now - timedelta(days=30)
        timeframe_filter = {'player_points__rounds__created_at__gte': start_date}
    elif timeframe == 'year':
        start_date = now - timedelta(days=365)
        timeframe_filter = {'player_points__rounds__created_at__gte': start_date}
    
    # Apply timeframe filter if it's not 'all'
    if timeframe_filter:
        players_query = players_query.filter(**timeframe_filter)
    
    # Annotate with statistics
    players_query = players_query.annotate(
        total_points=Coalesce(Sum('player_points__points'), Value(0)),
        games_played=Count('games', distinct=True),
        rounds_played=Count('player_points__rounds', distinct=True),
        rounds_won=Count(
            Case(
                When(player_points__points__gt=0, then=1),
                output_field=FloatField()
            )
        )
    )
    
    # Calculate derived metrics
    players_query = players_query.annotate(
        win_rate=Case(
            When(rounds_played__gt=0, 
                 then=F('rounds_won') * 1.0 / F('rounds_played')),
            default=Value(0.0),
            output_field=FloatField()
        ),
        avg_points_per_game=Case(
            When(games_played__gt=0, 
                 then=F('total_points') * 1.0 / F('games_played')),
            default=Value(0.0),
            output_field=FloatField()
        )
    )
    
    # Filter out players with no games
    players_query = players_query.filter(games_played__gt=0)
    
    # Order by requested metric
    if metric == 'total_points':
        players_query = players_query.order_by('-total_points')
    elif metric == 'win_rate':
        players_query = players_query.order_by('-win_rate')
    elif metric == 'avg_points_per_game':
        players_query = players_query.order_by('-avg_points_per_game')
    else:
        return Response(
            {'error': f'Invalid metric: {metric}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get top N players
    top_players = players_query[:limit]
    
    # Add rank
    ranked_players = []
    for i, player in enumerate(top_players, 1):
        player.rank = i
        ranked_players.append(player)
    
    # Serialize the results
    serializer = PlayerLeaderboardEntrySerializer(ranked_players, many=True)
    
    return Response({'leaderboard': serializer.data})

@api_view(['GET'])
def get_player_win_loss(request, player_id):
    """
    Get detailed win/loss statistics for a player
    
    Query Parameters:
    - timeframe: Time period filter
    - game_type: Filter by game type
    - with_player: See performance with specific teammate
    """
    try:
        # Validate player exists
        player = Player.objects.get(player_id=player_id)
    except Player.DoesNotExist:
        return Response({'error': 'Player not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    # Parse query parameters
    timeframe = request.GET.get('timeframe', 'all')
    game_type = request.GET.get('game_type', None)
    with_player_id = request.GET.get('with_player', None)
    
    # Get all player points for this player
    player_points_query = PlayerPoints.objects.filter(player=player)
    
    # Apply timeframe filter
    if timeframe != 'all':
        now = datetime.now()
        if timeframe == 'month':
            start_date = now - timedelta(days=30)
        elif timeframe == 'year':
            start_date = now - timedelta(days=365)
        else:
            return Response(
                {'error': f'Invalid timeframe: {timeframe}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        player_points_query = player_points_query.filter(
            rounds__created_at__gte=start_date
        )
    
    # Get summary statistics
    total_rounds = player_points_query.filter(rounds__isnull=False).count()
    # Count distinct games to avoid duplicates
    total_games = player_points_query.filter(games__isnull=False).values('games').distinct().count()
    
    # Count wins and losses
    wins = player_points_query.filter(points__gt=0).count()
    losses = player_points_query.filter(points__lte=0).count()
    
    # Calculate win rate
    win_rate = wins / total_rounds if total_rounds > 0 else 0
    
    # Calculate average points per round
    avg_points = player_points_query.aggregate(avg=Avg('points'))['avg'] or 0
    
    summary = {
        'games_played': total_games,
        'rounds_played': total_rounds,
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate, 3),
        'average_points_per_round': round(avg_points, 1)
    }
    
    # Get statistics by game type
    by_game_type = {}
    
    # For normal games
    normal_rounds = player_points_query.filter(
        rounds__was_solo_by__isnull=True,
        rounds__was_pflichtsolo_by__isnull=True
    )
    normal_wins = normal_rounds.filter(points__gt=0).count()
    normal_total = normal_rounds.count()
    
    by_game_type['normal'] = {
        'rounds_played': normal_total,
        'wins': normal_wins,
        'losses': normal_total - normal_wins,
        'win_rate': round(normal_wins / normal_total if normal_total > 0 else 0, 3)
    }
    
    # For solo games
    solo_rounds = player_points_query.filter(
        rounds__was_solo_by=player
    )
    solo_wins = solo_rounds.filter(points__gt=0).count()
    solo_total = solo_rounds.count()
    
    by_game_type['solo'] = {
        'rounds_played': solo_total,
        'wins': solo_wins,
        'losses': solo_total - solo_wins,
        'win_rate': round(solo_wins / solo_total if solo_total > 0 else 0, 3)
    }
    
    # For pflichtsolo games
    pflichtsolo_rounds = player_points_query.filter(
        rounds__was_pflichtsolo_by=player
    )
    pflichtsolo_wins = pflichtsolo_rounds.filter(points__gt=0).count()
    pflichtsolo_total = pflichtsolo_rounds.count()
    
    by_game_type['pflichtsolo'] = {
        'rounds_played': pflichtsolo_total,
        'wins': pflichtsolo_wins,
        'losses': pflichtsolo_total - pflichtsolo_wins,
        'win_rate': round(pflichtsolo_wins / pflichtsolo_total if pflichtsolo_total > 0 else 0, 3)
    }
    
    # Get statistics by team if with_player is specified
    by_team = []
    if with_player_id:
        try:
            teammate = Player.objects.get(player_id=with_player_id)
            
            # Find rounds where both players participated
            rounds_together_ids = Round.objects.filter(
                player_points__player=player
            ).filter(
                player_points__player=teammate
            ).values_list('id', flat=True)
            
            # Get player points for these rounds
            points_in_rounds_together = player_points_query.filter(
                rounds__id__in=rounds_together_ids
            )
            
            # Calculate statistics
            rounds_together = points_in_rounds_together.count()
            wins_together = points_in_rounds_together.filter(points__gt=0).count()
            win_rate_together = wins_together / rounds_together if rounds_together > 0 else 0
            
            by_team.append({
                'with_player_name': teammate.name,
                'rounds_together': rounds_together,
                'win_rate': round(win_rate_together, 3)
            })
        except Player.DoesNotExist:
            pass  # Ignore if teammate not found
    
    # Construct the response
    response_data = {
        'summary': summary,
        'by_game_type': by_game_type,
        'by_team': by_team
    }
    
    return Response(response_data)

@api_view(['GET'])
def get_game_type_performance(request, player_id):
    """
    Analyze performance across different game types
    
    Query Parameters:
    - timeframe: Time period filter
    """
    try:
        # Validate player exists
        player = Player.objects.get(player_id=player_id)
    except Player.DoesNotExist:
        return Response({'error': 'Player not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    # Parse query parameters
    timeframe = request.GET.get('timeframe', 'all')
    
    # Get all player points for this player
    player_points_query = PlayerPoints.objects.filter(player=player)
    
    # Apply timeframe filter
    if timeframe != 'all':
        now = datetime.now()
        if timeframe == 'month':
            start_date = now - timedelta(days=30)
        elif timeframe == 'year':
            start_date = now - timedelta(days=365)
        else:
            return Response(
                {'error': f'Invalid timeframe: {timeframe}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        player_points_query = player_points_query.filter(
            rounds__created_at__gte=start_date
        )
    
    # Initialize response structure
    by_game_type = {}
    
    # Analyze normal game performance
    normal_rounds = player_points_query.filter(
        rounds__was_solo_by__isnull=True,
        rounds__was_pflichtsolo_by__isnull=True
    )
    normal_count = normal_rounds.count()
    
    if normal_count > 0:
        normal_wins = normal_rounds.filter(points__gt=0).count()
        normal_avg_points = normal_rounds.aggregate(avg=Avg('points'))['avg'] or 0
        
        # Find best normal round
        best_normal_round = normal_rounds.order_by('-points').first()
        best_normal = None
        if best_normal_round:
            best_normal = {
                'points': best_normal_round.points,
                'date': best_normal_round.rounds.first().created_at if best_normal_round.rounds.first() else None
            }
        
        by_game_type['normal'] = {
            'rounds_played': normal_count,
            'win_rate': round(normal_wins / normal_count, 3),
            'average_points': round(normal_avg_points, 1),
            'best_round': best_normal
        }
    else:
        by_game_type['normal'] = {
            'rounds_played': 0,
            'win_rate': 0,
            'average_points': 0,
            'best_round': None
        }
    
    # Analyze solo game performance
    solo_rounds = player_points_query.filter(
        rounds__was_solo_by=player
    )
    solo_count = solo_rounds.count()
    
    if solo_count > 0:
        solo_wins = solo_rounds.filter(points__gt=0).count()
        solo_avg_points = solo_rounds.aggregate(avg=Avg('points'))['avg'] or 0
        
        # Find best solo round
        best_solo_round = solo_rounds.order_by('-points').first()
        best_solo = None
        if best_solo_round:
            best_solo = {
                'points': best_solo_round.points,
                'date': best_solo_round.rounds.first().created_at if best_solo_round.rounds.first() else None
            }
        
        by_game_type['solo'] = {
            'rounds_played': solo_count,
            'win_rate': round(solo_wins / solo_count, 3),
            'average_points': round(solo_avg_points, 1),
            'best_round': best_solo
        }
    else:
        by_game_type['solo'] = {
            'rounds_played': 0,
            'win_rate': 0,
            'average_points': 0,
            'best_round': None
        }
    
    # Analyze pflichtsolo game performance
    pflichtsolo_rounds = player_points_query.filter(
        rounds__was_pflichtsolo_by=player
    )
    pflichtsolo_count = pflichtsolo_rounds.count()
    
    if pflichtsolo_count > 0:
        pflichtsolo_wins = pflichtsolo_rounds.filter(points__gt=0).count()
        pflichtsolo_avg_points = pflichtsolo_rounds.aggregate(avg=Avg('points'))['avg'] or 0
        
        # Find best pflichtsolo round
        best_pflichtsolo_round = pflichtsolo_rounds.order_by('-points').first()
        best_pflichtsolo = None
        if best_pflichtsolo_round:
            best_pflichtsolo = {
                'points': best_pflichtsolo_round.points,
                'date': best_pflichtsolo_round.rounds.first().created_at if best_pflichtsolo_round.rounds.first() else None
            }
        
        by_game_type['pflichtsolo'] = {
            'rounds_played': pflichtsolo_count,
            'win_rate': round(pflichtsolo_wins / pflichtsolo_count, 3),
            'average_points': round(pflichtsolo_avg_points, 1),
            'best_round': best_pflichtsolo
        }
    else:
        by_game_type['pflichtsolo'] = {
            'rounds_played': 0,
            'win_rate': 0,
            'average_points': 0,
            'best_round': None
        }
    
    return Response({'by_game_type': by_game_type})

@api_view(['GET'])
def get_player_trends(request, player_id):
    """
    Track performance evolution over time
    
    Query Parameters:
    - metric: What to analyze (points, win_rate, games_played)
    - interval: Time grouping (day, week, month)
    - start_date/end_date: Analysis period
    """
    try:
        # Validate player exists
        player = Player.objects.get(player_id=player_id)
    except Player.DoesNotExist:
        return Response({'error': 'Player not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    # Parse query parameters
    metric = request.GET.get('metric', 'points')
    interval = request.GET.get('interval', 'month')
    
    # Validate metric
    valid_metrics = ['points', 'win_rate', 'games_played']
    if metric not in valid_metrics:
        return Response(
            {'error': f'Invalid metric. Must be one of: {", ".join(valid_metrics)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate interval
    valid_intervals = ['day', 'week', 'month']
    if interval not in valid_intervals:
        return Response(
            {'error': f'Invalid interval. Must be one of: {", ".join(valid_intervals)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Parse date range
    try:
        start_date = request.GET.get('start_date', None)
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            # Default to 6 months ago
            start_date = datetime.now() - timedelta(days=180)
        
        end_date = request.GET.get('end_date', None)
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = datetime.now()
    except ValueError:
        return Response(
            {'error': 'Invalid date format. Use YYYY-MM-DD'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get rounds within the date range
    rounds = Round.objects.filter(
        player_points__player=player,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).order_by('created_at')
    
    if not rounds.exists():
        return Response(
            {'error': 'No data available for the specified time period'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Group data by interval
    trend_data = []
    
    # Determine the interval formatting and grouping
    if interval == 'day':
        date_format = '%Y-%m-%d'
        delta = timedelta(days=1)
    elif interval == 'week':
        date_format = '%Y-%W'  # Year-Week number
        delta = timedelta(days=7)
    else:  # month
        date_format = '%Y-%m'
        delta = timedelta(days=30)
    
    # Create periods from start_date to end_date
    current_date = start_date
    while current_date <= end_date:
        period_key = current_date.strftime(date_format)
        
        # For week interval, we need special handling
        if interval == 'week':
            # strftime gives the week number, but we want a more readable format
            week_number = int(period_key.split('-')[1])
            period_key = f"{current_date.year}-W{week_number:02d}"
        
        # Get next period end
        if interval == 'month':
            # Handle month transitions properly
            if current_date.month == 12:
                next_period = datetime(current_date.year + 1, 1, 1)
            else:
                next_period = datetime(current_date.year, current_date.month + 1, 1)
        else:
            next_period = current_date + delta
        
        # Get rounds in this period
        period_rounds = rounds.filter(
            created_at__gte=current_date,
            created_at__lt=next_period
        )
        
        # Calculate metrics for this period
        period_data = {
            'period': period_key,
            'value': 0,
            'games_played': 0
        }
        
        if period_rounds.exists():
            # Count unique games in this period
            games_in_period = period_rounds.values('game').distinct().count()
            period_data['games_played'] = games_in_period
            
            if metric == 'points':
                # Sum points for player in this period
                points_sum = PlayerPoints.objects.filter(
                    player=player,
                    rounds__in=period_rounds
                ).aggregate(total=Sum('points'))['total'] or 0
                
                period_data['value'] = points_sum
            
            elif metric == 'win_rate':
                # Calculate win rate for this period
                player_points_in_period = PlayerPoints.objects.filter(
                    player=player,
                    rounds__in=period_rounds
                )
                total_rounds = player_points_in_period.count()
                wins = player_points_in_period.filter(points__gt=0).count()
                
                win_rate = wins / total_rounds if total_rounds > 0 else 0
                period_data['value'] = round(win_rate, 3)
            
            elif metric == 'games_played':
                period_data['value'] = games_in_period
        
        trend_data.append(period_data)
        current_date = next_period
    
    # Filter out periods with no games if there are enough data points
    if len(trend_data) > 3:
        trend_data = [data for data in trend_data if data['games_played'] > 0]
    
    # Calculate trend analysis
    trend_analysis = {}
    
    if trend_data:
        # Find best and worst periods
        non_zero_periods = [data for data in trend_data if data['games_played'] > 0]
        
        if non_zero_periods:
            best_period = max(non_zero_periods, key=lambda x: x['value'])
            worst_period = min(non_zero_periods, key=lambda x: x['value'])
            
            trend_analysis['best_period'] = best_period['period']
            trend_analysis['worst_period'] = worst_period['period']
            
            # Calculate overall trend
            if len(non_zero_periods) >= 2:
                first_value = non_zero_periods[0]['value']
                last_value = non_zero_periods[-1]['value']
                
                if first_value == 0:
                    growth_rate = None
                else:
                    growth_rate = (last_value - first_value) / first_value if first_value != 0 else None
                
                if growth_rate is not None:
                    trend_analysis['growth_rate'] = f"{round(growth_rate * 100, 1)}%"
                    
                    if growth_rate > 0:
                        trend_analysis['overall_trend'] = 'increasing'
                    elif growth_rate < 0:
                        trend_analysis['overall_trend'] = 'decreasing'
                    else:
                        trend_analysis['overall_trend'] = 'stable'
    
    # Construct the response
    response_data = {
        'metric': metric,
        'interval': interval,
        'data': trend_data,
        'trend_analysis': trend_analysis
    }
    
    return Response(response_data)