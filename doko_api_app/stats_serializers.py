from rest_framework import serializers
from .models import Game, Round, PlayerPoints, Player

class BestRoundSerializer(serializers.ModelSerializer):
    """Serializer for displaying a player's best rounds"""
    round_id = serializers.IntegerField(source='id')
    game_id = serializers.UUIDField(source='game.game_id')
    game_name = serializers.CharField(source='game.game_name')
    date = serializers.DateTimeField(source='created_at')
    points = serializers.SerializerMethodField()
    bock_multiplier = serializers.IntegerField()
    game_type = serializers.SerializerMethodField()
    opponents = serializers.SerializerMethodField()
    
    class Meta:
        model = Round
        fields = [
            'round_id', 'game_id', 'game_name', 'date', 
            'points', 'bock_multiplier', 'game_type', 'opponents'
        ]
    
    def get_points(self, obj):
        """Get the points for the specific player"""
        player_id = self.context.get('player_id')
        player_points = obj.player_points.filter(player__player_id=player_id).first()
        return player_points.points if player_points else 0
    
    def get_game_type(self, obj):
        """Determine the game type (normal, solo, pflichtsolo)"""
        player_id = self.context.get('player_id')
        if obj.was_solo_by and str(obj.was_solo_by.player_id) == player_id:
            return 'solo'
        elif obj.was_pflichtsolo_by and str(obj.was_pflichtsolo_by.player_id) == player_id:
            return 'pflichtsolo'
        return 'normal'
    
    def get_opponents(self, obj):
        """Get the names of opponents in the round"""
        player_id = self.context.get('player_id')
        players = [
            player_point.player.name 
            for player_point in obj.player_points.all()
            if str(player_point.player.player_id) != player_id
        ]
        return players

class PlayerLeaderboardEntrySerializer(serializers.ModelSerializer):
    """Serializer for player leaderboard entries"""
    player_id = serializers.UUIDField()
    player_name = serializers.CharField(source='name')
    total_points = serializers.IntegerField()
    games_played = serializers.IntegerField()
    win_rate = serializers.FloatField()
    avg_points_per_game = serializers.FloatField()
    
    class Meta:
        model = Player
        fields = [
            'player_id', 'player_name', 'total_points', 
            'games_played', 'win_rate', 'avg_points_per_game'
        ]

class WinLossStatsSerializer(serializers.Serializer):
    """Serializer for win/loss statistics"""
    summary = serializers.DictField()
    by_game_type = serializers.DictField()
    by_team = serializers.ListField()

class GameTypePerformanceSerializer(serializers.Serializer):
    """Serializer for game type performance statistics"""
    by_game_type = serializers.DictField()

class TrendDataPointSerializer(serializers.Serializer):
    """Serializer for trend data points"""
    period = serializers.CharField()
    value = serializers.FloatField()
    games_played = serializers.IntegerField()

class TrendAnalysisSerializer(serializers.Serializer):
    """Serializer for trend analysis"""
    metric = serializers.CharField()
    interval = serializers.CharField()
    data = TrendDataPointSerializer(many=True)
    trend_analysis = serializers.DictField()