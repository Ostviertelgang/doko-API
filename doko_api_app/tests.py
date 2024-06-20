from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from .models import Game, Player, PlayerPoints, Round
#from ..serializers import GameSerializer, PlayerSerializer, PlayerPointsSerializer, RoundSerializer


class ViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create some objects for testing
        self.test_players = [Player.objects.create(name=f'Test Player {i}') for i in range(4)]
        self.test_game = None
        data = {
            'game_name': 'Test Game',
            'players': [player.player_id for player in self.test_players]
        }
        response = self.client.post(reverse('game-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.test_game = Game.objects.get(game_id=response.data['game_id'])

    def test_create_player(self):
        data = {
            'name': 'Test Player'
        }
        response = self.client.post(reverse('player-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_round_solo(self):
        """Test the /games/<game_id>/add_round/ endpoint with a solo round."""
        data = {
            'winning_players': [str(self.test_players[0].player_id)],
            'losing_players': [str(self.test_players[1].player_id), str(self.test_players[2].player_id),
                                str(self.test_players[3].player_id)],
            'points': 10,
            'caused_bock_parrallel': 0,
        }
        response = self.client.post(reverse('add_round', args=[str(self.test_game.game_id)]), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Round.objects.count(), 1)
        self.assertEqual(PlayerPoints.objects.count(), 4)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[0]).points, 30)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[1]).points, -10)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[2]).points, -10)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[3]).points, -10)