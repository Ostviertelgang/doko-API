from django.contrib.auth.models import Group, User
from rest_framework import serializers
from .models import Game, Round, PlayerPoints, Player
from rest_framework import serializers


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['player_id', 'name']


class PlayerPointsSerializer(serializers.ModelSerializer):
    #player = PlayerSerializer()
    player = serializers.SlugRelatedField(slug_field='player_id', queryset=Player.objects.all())
    game_id = serializers.SerializerMethodField()
    round_id = serializers.SerializerMethodField()
    game_created_at = serializers.SerializerMethodField()
    game_name = serializers.SerializerMethodField()
    round_created_at = serializers.SerializerMethodField()

    class Meta:
        model = PlayerPoints
        #fields = ['player', 'points', 'game_id', 'round_id']
        fields = ['player', 'points', 'game_id', 'round_id', 'game_created_at', 'game_name', 'round_created_at']

    def get_game_id(self, obj):
        game = obj.games.first()
        return game.game_id if game else None

    def get_round_id(self, obj):
        round = obj.rounds.first()
        return round.id if round else None

    def get_player_id(self, obj):
        return obj.player.player_id

    def get_game_created_at(self, obj):
        game = obj.games.first()
        return game.created_at if game else None

    def get_game_name(self, obj):
        game = obj.games.first()
        return game.game_name if game else None

    def get_round_created_at(self, obj):
        round = obj.rounds.first()
        return round.created_at if round else None


class GameSerializer(serializers.ModelSerializer):
    # return all the player in the game
    players = serializers.SlugRelatedField(many=True, slug_field='player_id', queryset=Player.objects.all())
    player_points = PlayerPointsSerializer(many=True, read_only=True)
    class Meta:
        model = Game
        fields = ['created_at', 'closed_at', 'update_at', 'game_id', 'game_name', 'is_closed',"player_points","players"]


class RoundSerializer(serializers.ModelSerializer):
    player_points = PlayerPointsSerializer(many=True, read_only=True)
    class Meta:
        model = Round
        fields = ['game', 'points', 'created_at', 'player_points', 'bocks_parallel', 'bock_multiplier']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']