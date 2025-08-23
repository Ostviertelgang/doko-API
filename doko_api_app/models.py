from django.db import models
from django.contrib.auth.models import User
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import JSONField

class Game(models.Model):
    """
    A game is a collection of rounds
    """
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(default=None, blank=True, null=True)
    update_at = models.DateTimeField(auto_now=True)
    game_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    game_name = models.CharField(max_length=200)
    is_closed = models.BooleanField(default=False)
    players = models.ManyToManyField('Player', related_name='games', blank=True)
    player_points = models.ManyToManyField('PlayerPoints', related_name='games', blank=True)
    bock_round_status = JSONField(default=list, blank=True)
    flag_removed = models.BooleanField(default=False)

    def __str__(self):
        return f"Game {self.game_id}: {self.game_name}"

    def get_all_rounds(self):
        return self.rounds.all()

class Player(models.Model):
    """
    A player represents a user in the game system
    """
    name = models.CharField(max_length=200)
    player_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='player')
    join_date = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    flag_removed = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def is_admin(self):
        return self.user and self.user.groups.filter(name='Admin').exists()

class Round(models.Model):
    game = models.ForeignKey(Game, related_name='rounds', on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    player_points = models.ManyToManyField('PlayerPoints', related_name='rounds', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    bock_multiplier = models.IntegerField(default=1)
    bocks_parallel = models.IntegerField(default=0)
    was_solo_by = models.ForeignKey(Player, related_name='solo_rounds', on_delete=models.SET_NULL, blank=True, null=True, to_field='player_id')
    was_pflichtsolo_by = models.ForeignKey(Player, related_name='pflichtsolo_rounds', on_delete=models.SET_NULL, blank=True, null=True, to_field='player_id')

    def __str__(self):
        return f"Round {self.id} of Game {self.game_id}"

class PlayerPoints(models.Model):
    player = models.ForeignKey(Player, related_name='player_points', on_delete=models.CASCADE)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.player.name} has {self.points} points"
