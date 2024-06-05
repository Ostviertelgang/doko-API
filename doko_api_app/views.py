from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets

from doko_api_app.serializers import GroupSerializer, UserSerializer


from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Game, Round, PlayerPoints, Player
from .serializers import GameSerializer, RoundSerializer, PlayerPointsSerializer, PlayerSerializer
from django.http import HttpResponse
import pandas as pd
import datetime


@api_view(['POST'])
def undo_round(request, game_id):
    """
    Undo the last round of a game
    todo maybe must be considered in bockrunde calculation
    :param request:
    :return:
    """
    try:
        game = Game.objects.get(game_id=game_id)
    except Game.DoesNotExist:
        return Response({'error': 'Game not found.'}, status=404)

    rounds = game.get_all_rounds()
    print(rounds.first())
    if not rounds.exists():
        return Response({'error': 'No rounds to undo.'}, status=404)

    round = rounds.last()
    player_points = round.player_points.all()
    for player_point in player_points:
        player_point.delete()
        player_point.save()

    round.delete()
    round.save()

    serializer = RoundSerializer(round)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def add_round(request, game_id):
    """
    Make a Round object, add the player points objects and attach it to a game before returning the round object
    :param request:
    :return:
    """
    #game_id = request.data.get('game_id')
    winning_players = request.data.get('winning_players')
    losing_players = request.data.get('losing_players')
    points = request.data.get('points')

    try:
        game = Game.objects.get(game_id=game_id)
    except Game.DoesNotExist:
        return Response({'error': 'Game not found.'}, status=404)

    round = Round.objects.create(game=game)

    if len(winning_players) == 1:
        is_solo = True
    else:
        is_solo = False

    for player_id in winning_players:
        player = Player.objects.get(player_id=player_id)
        if is_solo:
            player_points = PlayerPoints.objects.create(player=player, points=points * 3)
        else:
            player_points = PlayerPoints.objects.create(player=player, points=points)
        round.player_points.add(player_points)

    for player_id in losing_players:
        player = Player.objects.get(player_id=player_id)
        player_points = PlayerPoints.objects.create(player=player, points=points * -1)
        round.player_points.add(player_points)

    round.save()
    game.save()

    serializer = RoundSerializer(round)
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
    df = pd.DataFrame(columns=player_names+['game_id', 'game_name', 'is_closed', 'created_at', 'closed_at'])
    for game in games:
        player_points = game.player_points.all()
        player_points_dict = {player_point.player.name: player_point.points for player_point in player_points}
        player_points_dict.update({'game_id': game.game_id, 'game_name': game.game_name, 'is_closed': game.is_closed,
                                   'created_at': game.created_at, 'closed_at': game.closed_at})
        df = pd.concat([df, pd.DataFrame(player_points_dict, index=[0])], ignore_index=True)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="doko_export.csv"'
    df.to_csv(path_or_buf=response, index=False)
    return response

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
        amount_positive = 0
        positive_player = None
        player_points_round = round.player_points.all()
        for player_point in player_points_round:
            if player_point.points > 0:
                amount_positive += 1
                positive_player = player_point.player

        if amount_positive == 1:
            players_with_solo_done.append(positive_player)
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
    game.closed_at = datetime.datetime.now() # todo fix warning RuntimeWarning: DateTimeField Game.closed_at received a naive datetime (2024-06-05 17:24:57.134636) while time zone support is active.
    game.save()

    serializer = GameSerializer(game)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# get player pointsobejcts for a aplyer with timeframe with distincation for rounds /games, get  a link to the round or the game in the response
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

    game_points = PlayerPoints.objects.filter(player=player, games__isnull=False)
    serializer = PlayerPointsSerializer(game_points, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_player_points_for_round_stats(request, player_id):
    """
    Get player points method
    :param request:
    :return:
    """
    try:
        player = Player.objects.get(player_id=player_id)
    except Player.DoesNotExist:
        return Response({'error': 'Player not found.'}, status=404)

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


class PlayerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows players to be viewed or edited.
    """
    queryset = Player.objects.all().order_by('name')
    serializer_class = PlayerSerializer

    def get_object(self):
        """
        Returns the object the view is displaying.
        """
        # Get the UUID from the URL parameters
        uuid = self.kwargs.get('pk')

        # Retrieve the Player object that matches the UUID
        return Player.objects.get(player_id=uuid)
    #permission_classes = [permissions.IsAuthenticated]


class PlayerPointsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows player points to be viewed or edited.
    """
    queryset = PlayerPoints.objects.all().order_by('player')
    serializer_class = PlayerPointsSerializer
    #permission_classes = [permissions.IsAuthenticated]


class GameViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows games to be viewed or edited.
    """
    queryset = Game.objects.all().order_by('created_at')
    serializer_class = GameSerializer


    def get_object(self):
        """
        Returns the object the view is displaying.
        """
        # Get the UUID from the URL parameters
        uuid = self.kwargs.get('pk')

        # Retrieve the Game object that matches the UUID
        return Game.objects.get(game_id=uuid)
    #permission_classes = [permissions.IsAuthenticated]

class RoundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows rounds to be viewed or edited.
    """
    queryset = Round.objects.all().order_by('created_at')
    serializer_class = RoundSerializer
    #permission_classes = [permissions.IsAuthenticated]

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]