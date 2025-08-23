from django.shortcuts import render
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from datetime import datetime
from .points_visualization import PointsVisualizer
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from django.http import HttpResponse
import pandas as pd
from django.utils import timezone

from .models import Game, Round, PlayerPoints, Player
from .serializers import (
    GameSerializer, RoundSerializer, PlayerPointsSerializer,
    PlayerSerializer, UserSerializer, GroupSerializer,
    CompactPlayerPointsSerializer
)

class GenerateAuthToken(ObtainAuthToken):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })

class PlayerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows players to be viewed or edited.
    """
    queryset = Player.objects.filter(flag_removed=False).order_by('name')
    serializer_class = PlayerSerializer
    lookup_field = 'player_id'

    def get_object(self):
        uuid = self.kwargs.get(self.lookup_field)
        return Player.objects.get(player_id=uuid)

    def destroy(self, request, *args, **kwargs):
        player = self.get_object()
        player.flag_removed = True
        player.name = "REMOVED USER"
        player.save()
        return Response(
            {"detail": "Deletion not allowed, deleted player name"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

class GameViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows games to be viewed or edited.
    """
    queryset = Game.objects.filter(flag_removed=False).order_by('-created_at')
    serializer_class = GameSerializer
    lookup_field = 'game_id'

    def get_object(self):
        uuid = self.kwargs.get(self.lookup_field)
        return Game.objects.get(game_id=uuid)

    def destroy(self, request, *args, **kwargs):
        game = self.get_object()
        game.flag_removed = True
        game.game_name = "REMOVED GAME"
        game.save()
        return Response(
            {"detail": "Deletion not allowed, set to removed"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
        
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Create a list to hold the response data
        response_data = []

        # Iterate over the queryset
        for game in queryset:
            # Serialize the Game instance
            serializer = self.get_serializer(game)

            # Retrieve the related PlayerPoints instances
            player_points = PlayerPoints.objects.filter(games__game_id=game.game_id)

            # Serialize the PlayerPoints instances using the custom serializer
            player_points_serializer = CompactPlayerPointsSerializer(player_points, many=True)

            # Add the serialized PlayerPoints data to the serialized Game data
            game_data = serializer.data
            game_data['player_points'] = player_points_serializer.data

            # Add the game data to the response data
            response_data.append(game_data)

        return Response(response_data)


class PlayerPointsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows player points to be viewed or edited.
    """
    queryset = PlayerPoints.objects.all().order_by('player')
    serializer_class = PlayerPointsSerializer


class RoundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows rounds to be viewed or edited.
    """
    queryset = Round.objects.all().order_by('created_at')
    serializer_class = RoundSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'create' or settings.DISABLE_AUTHENTICATION:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user
        user = User.objects.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        # Create linked player
        player = Player.objects.create(
            name=user.username,
            user=user,
            join_date=timezone.now(),
            last_active=timezone.now()
        )
        
        # Add to Player group by default
        player_group = Group.objects.get(name='Player')
        user.groups.add(player_group)
        
        serializer = self.get_serializer(user)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

# V1 API Endpoints for backward compatibility

@api_view(['GET'])
def get_bock_status(request, game_id):
    """
    Get the bock status of a game
    :param request:
    :return:
    """
    try:
        game = Game.objects.get(game_id=game_id)
    except Game.DoesNotExist:
        return Response({'error': 'Game not found.'}, status=404)

    return Response({'bock_round_status': game.bock_round_status}, status=status.HTTP_200_OK)

@api_view(['POST'])
def undo_round(request, game_id):
    """
    Undo the last round of a game
    :param request:
    :return:
    """
    try:
        game = Game.objects.get(game_id=game_id)
    except Game.DoesNotExist:
        return Response({'error': 'Game not found.'}, status=404)

    rounds = game.get_all_rounds()
    if not rounds.exists():
        return Response({'error': 'No rounds to undo.'}, status=404)

    round = rounds.last()
    player_points = round.player_points.all()
    for player_point in player_points:
        player_point.delete()

    game.bock_round_status = [remaining_bock_rounds + 1 for remaining_bock_rounds in game.bock_round_status]
    new_bock_status = []
    for bock_status in game.bock_round_status:
        if bock_status <= len(game.players.all()):
            new_bock_status.append(bock_status)
    game.bock_round_status = new_bock_status
    round.delete()
    game.save()

    return Response({'message': 'Round undone.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def add_round(request, game_id):
    """
    Make a Round object, add the player points objects and attach it to a game before returning the round object
    :param request:
    :return:
    """
    winning_players = request.data.get('winning_players')
    losing_players = request.data.get('losing_players')
    points = request.data.get('points')
    caused_bock_parrallel = request.data.get('caused_bock_parrallel')
    was_pflichtsolo_by = request.data.get('was_pflichtsolo_by', False)

    try:
        game = Game.objects.get(game_id=game_id)
    except Game.DoesNotExist:
        return Response({'error': 'Game not found.'}, status=404)

    round_obj = Round.objects.create(game=game)

    round_obj.bocks_parallel = len(game.bock_round_status) # this is how many bocks are going
    round_obj.bock_multiplier = 2 ** round_obj.bocks_parallel

    # only write was_pflichjt_solo_by if it is the first pflichtsolo of that player
    if was_pflichtsolo_by and not round_obj.game.get_all_rounds().filter(was_pflichtsolo_by=was_pflichtsolo_by).exists():
        round_obj.was_pflichtsolo_by = Player.objects.get(player_id=was_pflichtsolo_by)

    if len(winning_players) == 1:
        is_solo = True
        round_obj.was_solo_by = Player.objects.get(player_id=winning_players[0])
    else:
        is_solo = False

    for player_id in winning_players:
        player = Player.objects.get(player_id=player_id)
        if is_solo:
            player_points = PlayerPoints.objects.create(player=player, points=points * 3 * round_obj.bock_multiplier)
        else:
            player_points = PlayerPoints.objects.create(player=player, points=points * round_obj.bock_multiplier)
        round_obj.player_points.add(player_points)

    for player_id in losing_players:
        player = Player.objects.get(player_id=player_id)
        player_points = PlayerPoints.objects.create(player=player, points=points * -1 * round_obj.bock_multiplier)
        round_obj.player_points.add(player_points)

    # decrease the bockrunden
    game.bock_round_status = [remaining_bock_rounds - 1 for remaining_bock_rounds in game.bock_round_status if
                              remaining_bock_rounds > 1]

    # add new bockrunden if needed
    # 4 players, add 4 bockrunden, 5 player 5 round etc.
    [game.bock_round_status.append(len(game.players.all())) for i in range(0,caused_bock_parrallel)]
    round_obj.save()
    game.save()

    serializer = RoundSerializer(round_obj)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def add_player_points_to_game(request, game_id):
    """
    Add player points to a game
    :param request:
    :return:
    """
    game = Game.objects.get(game_id=game_id)
    player_points_list = request.data

    for player_point in player_points_list:
        player = Player.objects.get(player_id=player_point.get('player_id'))
        points = player_point.get('points')
        player_points = PlayerPoints.objects.create(player=player, points=points)
        game.player_points.add(player_points)

    game.save()
    serializer = GameSerializer(game)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def make_csv_export(request):
    """
    Make a csv export
    :param request:
    :return:
    """
    games = Game.objects.all()
    players = Player.objects.all()
    player_names = [player.name for player in players]
    df = pd.DataFrame(columns=player_names+['game_id', 'game_name', 'is_closed', 'created_at', 'closed_at']) # if you ever add new ones, als add them below in the importer
    df = df.dropna(axis=1, how='all')
    for game in games:
        player_points = game.player_points.all()
        player_points_dict = {player_point.player.name: player_point.points for player_point in player_points}
        player_points_dict.update({'game_id': game.game_id, 'game_name': game.game_name, 'is_closed': game.is_closed,
                                   'created_at': game.created_at, 'closed_at': game.closed_at})
        player_points_df = pd.DataFrame(player_points_dict, index=[0])
        player_points_df = player_points_df.dropna(axis=1, how='all')
        df = pd.concat([df, player_points_df], ignore_index=True)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="doko_export.csv"'
    df.to_csv(path_or_buf=response, index=False)
    return response


file_param = openapi.Parameter('file', in_=openapi.IN_FORM, type=openapi.TYPE_FILE)
create_game_duplicates_based_on_ids_param = openapi.Parameter('create_game_duplicates_based_on_ids', in_=openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False)


@swagger_auto_schema(method='post', manual_parameters=[file_param, create_game_duplicates_based_on_ids_param])
@api_view(['POST'])
@parser_classes([FormParser, MultiPartParser])
def import_csv(request):
    """
    Import csv games previously exported
    :param request:
    :return:
    """
    import_metadata = {}

    csv_file = request.data['file']
    df = pd.read_csv(csv_file)
    create_game_duplicates_based_on_ids = request.data.get('create_game_duplicates_based_on_ids', False)

    if create_game_duplicates_based_on_ids == 'true' or create_game_duplicates_based_on_ids is True: # todo find the proper way to do this
        create_game_duplicates_based_on_ids = True
    else:
        create_game_duplicates_based_on_ids = False

    import_metadata["csv_length"] = len(df)

    predefined_columns = ['game_id', 'game_name', 'is_closed', 'created_at', 'closed_at']
    player_names = [col for col in df.columns if col not in predefined_columns]
    import_metadata["player_names"] = player_names
    games_create = 0
    players_created = 0

    for index, row in df.iterrows():
        game_id = row['game_id']
        game_name = row['game_name']
        is_closed = row['is_closed']
        created_at = row['created_at']
        if pd.isna(created_at):
            created_at = datetime.now() # if no created at is given, use now
        created_at = (pd.to_datetime(created_at))
        closed_at = row['closed_at']
        closed_at = (pd.to_datetime(closed_at))
        if pd.isna(closed_at):
            closed_at = None

        if create_game_duplicates_based_on_ids:
            #create with new id
            game = Game.objects.create(game_name=game_name, is_closed=is_closed, created_at=created_at, closed_at=closed_at)
            games_create += 1
        else:
            game, created = Game.objects.get_or_create(game_id=game_id, defaults={
                'game_name': game_name,
                'is_closed': is_closed,
                'created_at': created_at,
                'closed_at': closed_at
            })
            if created:
                games_create += 1

        for player_name in player_names:
            points = row[player_name]
            if pd.isna(points):
                continue
            player, created = Player.objects.get_or_create(name=player_name)
            if created:
                players_created += 1
            player_points = PlayerPoints.objects.create(player=player, points=points)
            game.player_points.add(player_points)

        game.save()
    import_metadata["games_created"] = games_create
    import_metadata["players_created"] = players_created
    import_metadata["status"] = "Import successful."
    return Response(import_metadata, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def get_players_with_pflichtsolo(request, game_id):
    """
    Get all players which have to still play their Pflichtsolo
    :param game_id:
    :return:
    """
    game = Game.objects.get(game_id=game_id)
    rounds = game.get_all_rounds()
    players_with_solo_done = []

    for round in rounds:
        if round.was_pflichtsolo_by:
            players_with_solo_done.append(round.was_pflichtsolo_by)
    players_in_game = game.players.all()
    players_with_solo_ahead = [player for player in players_in_game if player not in players_with_solo_done]
    serializer = PlayerSerializer(players_with_solo_ahead, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def commit_game(request, game_id):
    """
    Commit game method
    :param request:
    :return:
    """
    game = Game.objects.get(game_id=game_id)
    # get all the rounds for the game
    rounds = game.get_all_rounds()
    player_points_dict = {}

    for round in rounds:
        player_points_round = round.player_points.all()
        for player_point in player_points_round:
            if player_point.player.player_id in player_points_dict:
                player_points_dict[player_point.player.player_id] += player_point.points
            else:
                player_points_dict[player_point.player.player_id] = player_point.points

    for player_id, points in player_points_dict.items():
        player = Player.objects.get(player_id=player_id)
        player_points = PlayerPoints.objects.create(player=player, points=points)
        game.player_points.add(player_points)

    game.is_closed = True
    game.closed_at = timezone.now()
    game.save()

    serializer = GameSerializer(game)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# get player points object for a player with timeframe with distinction for rounds /games, get  a link to the round or the game in the response
@api_view(['GET'])
def get_player_points_for_game_stats(request, player_id):
    """
    Get player points method
    :param request:
    :return:
    """
    try:
        player = Player.objects.get(player_id=player_id)
    except Player.DoesNotExist:
        return Response({'error': 'Player not found.'}, status=404)
    # game removed flag is not set
    game_points = PlayerPoints.objects.filter(player=player, games__isnull=False, games__flag_removed=False)
    serializer = PlayerPointsSerializer(game_points, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_player_points_for_round_stats(request, player_id):
    """
    Get player points method
    :param request:
    :return:
    """
    game_id = request.data.get('game_id')
    try:
        player = Player.objects.get(player_id=player_id)
    except Player.DoesNotExist:
        return Response({'error': 'Player not found.'}, status=404)
    if game_id:
        round_points = PlayerPoints.objects.filter(player=player, rounds__isnull=False, rounds__game__game_id=game_id)
    else:
        round_points = PlayerPoints.objects.filter(player=player, rounds__isnull=False)
    serializer = PlayerPointsSerializer(round_points, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_all_rounds(request, game_id):
    try:
        game = Game.objects.get(game_id=game_id)
    except Game.DoesNotExist:
        return Response({'error': 'Game not found.'}, status=404)

    rounds = game.get_all_rounds()
    serializer = RoundSerializer(rounds, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_points_progression_gif(request, game_id):
    """
    Get animated GIF of points progression
    
    Args:
        request: HTTP request object
        game_id: UUID of the game
        
    Returns:
        HttpResponse with GIF image data
        
    Raises:
        HTTP 404: If game not found
        HTTP 400: If invalid parameters or visualization error
    """
    try:
        # Get duration parameter (optional)
        duration_ms = request.GET.get('duration', 500)
        try:
            duration_ms = int(duration_ms)
        except ValueError:
            return Response(
                {'error': 'Invalid duration parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get game and create visualizer
        try:
            game = Game.objects.get(game_id=game_id)
        except Game.DoesNotExist:
            return Response(
                {'error': 'Game not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            visualizer = PointsVisualizer(game)
            gif_data = visualizer.create_gif(duration_ms=duration_ms)

            # Create response with raw GIF data
            response = HttpResponse(content_type='image/gif')
            response['Content-Disposition'] = f'inline; filename="game_{game_id}_progression.gif"'
            response.write(gif_data.getvalue())
            return response

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        return Response(
            {'error': f'Error generating visualization: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # Ensure resources are cleaned up
        if 'gif_data' in locals():
            gif_data.close()


@api_view(['GET'])
def get_points_progression_image(request, game_id):
    """
    Get static image of points progression
    
    Args:
        request: HTTP request object
        game_id: UUID of the game
        
    Returns:
        HttpResponse with PNG image data
        
    Raises:
        HTTP 404: If game not found
        HTTP 400: If visualization error
    """
    try:
        # Get game and create visualizer
        try:
            game = Game.objects.get(game_id=game_id)
        except Game.DoesNotExist:
            return Response(
                {'error': 'Game not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            visualizer = PointsVisualizer(game)
            image_data = visualizer.create_static_image()

            response = HttpResponse(image_data.getvalue(), content_type='image/png')
            response['Content-Disposition'] = f'inline; filename="game_{game_id}_progression.png"'
            return response

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        return Response(
            {'error': f'Error generating visualization: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # Ensure resources are cleaned up
        if 'image_data' in locals():
            image_data.close()

# Game management endpoints (V2 simplified versions)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_round_v2(request, game_id):
    """Add a round to a game"""
    try:
        game = Game.objects.get(game_id=game_id)
    except Game.DoesNotExist:
        return Response(
            {'error': 'Game not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    round_obj = Round.objects.create(game=game)
    round_obj.save()
    serializer = RoundSerializer(round_obj)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def commit_game_v2(request, game_id):
    """Close a game and calculate final points"""
    try:
        game = Game.objects.get(game_id=game_id)
    except Game.DoesNotExist:
        return Response(
            {'error': 'Game not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    game.is_closed = True
    game.closed_at = timezone.now()
    game.save()

    serializer = GameSerializer(game)
    return Response(serializer.data, status=status.HTTP_200_OK)