from django.db import models
import uuid
# Create your models here.
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import JSONField

class Game(models.Model):
    """
    A game is a collection of rounds
    """
    created_at = models.DateTimeField(auto_now_add=True)
    #int game id
    closed_at = models.DateTimeField(default=None, blank=True, null=True)
    update_at = models.DateTimeField(auto_now=True)
    # primary key
    game_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    #string game name
    game_name = models.CharField(max_length=200)
    # is closed
    is_closed = models.BooleanField(default=False)
    #one game can have many players
    players = models.ManyToManyField('Player', related_name='games', blank=True)
    player_points = models.ManyToManyField('PlayerPoints', related_name='games', blank=True) # do not return to frontend
    bock_round_status = JSONField(default=list,blank=True)

    def __str__(self):
        return f"Game {self.game_id}: {self.game_name}"

    def get_all_rounds(self):
        return self.rounds.all()


class Player(models.Model):
    """
    A player is a user
    """
    #game = models.ForeignKey(Game, related_name='players', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    player_id =models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        """
        String representation of the player
        :return:
        """
        return self.name


class Round(models.Model):
    game = models.ForeignKey(Game, related_name='rounds', on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    # one round can have many playerpoints
    player_points = models.ManyToManyField('PlayerPoints', related_name='rounds', blank=True) # do not return to frontend
    created_at = models.DateTimeField(auto_now_add=True)
    bock_multiplier = models.IntegerField(default=1) #1 normal, 2 bock, 4 doubble bock, 8, 16
    bocks_parallel = models.IntegerField(default=0) # 0 bo bock, 1 bock, 2 doubble bock

    def __str__(self):
        """
        String representation of the round
        :return:
        """
        return f"Round {self.id} of Game {self.game_id}"


class PlayerPoints(models.Model):
    player = models.ForeignKey(Player, related_name='player_points', on_delete=models.CASCADE)
    points = models.IntegerField(default=0)


    def __str__(self):
        return f"{self.player.name} has {self.points} points"

#019ee97c-9c6b-4ebb-9d8b-138d8c32e504
"""
[{
    "player_id": "fed9589d-400e-4bff-9d98-6d983136a372",
    "points": 2
}]

"""