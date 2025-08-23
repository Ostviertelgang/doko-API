from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from doko_api_app.models import Player, Game, Round, PlayerPoints
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
from datetime import datetime, timedelta
import json

class V2EndpointsTest(TestCase):
    def setUp(self):
        """Set up test data with a proper 4-player Doppelkopf game."""
        # Create test user and get JWT token
        self.user = User.objects.create_user(username='testuser', password='testpass')
        refresh = RefreshToken.for_user(self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        # Create 4 players
        self.players = [
            Player.objects.create(name=f'Player {i+1}')
            for i in range(4)
        ]

        # Create a game
        data = {
            'game_name': 'Test Doppelkopf Game',
            'players': [str(player.player_id) for player in self.players]
        }
        response = self.client.post(reverse('game-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.game = Game.objects.get(game_id=response.data['game_id'])

    def add_normal_round(self, winners, losers, points=1, bock_parallel=0):
        """Add a normal round (2 winners vs 2 losers)."""
        data = {
            'winning_players': [str(p.player_id) for p in winners],
            'losing_players': [str(p.player_id) for p in losers],
            'points': points,
            'caused_bock_parrallel': bock_parallel
        }
        response = self.client.post(
            reverse('add_round', args=[str(self.game.game_id)]),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def add_solo_round(self, winner, losers, points=1, bock_parallel=0, is_pflichtsolo=False):
        """Add a solo round (1 winner vs 3 losers)."""
        data = {
            'winning_players': [str(winner.player_id)],
            'losing_players': [str(p.player_id) for p in losers],
            'points': points,
            'caused_bock_parrallel': bock_parallel,
            'was_pflichtsolo_by': str(winner.player_id) if is_pflichtsolo else None
        }
        response = self.client.post(
            reverse('add_round', args=[str(self.game.game_id)]),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def test_game_points(self):
        """Test game points endpoint."""
        # Add various rounds
        self.add_normal_round(
            winners=[self.players[0], self.players[1]],
            losers=[self.players[2], self.players[3]],
            points=2
        )
        
        self.add_solo_round(
            winner=self.players[0],
            losers=[self.players[1], self.players[2], self.players[3]],
            points=3
        )

        # Commit the game to create game points
        response = self.client.post(reverse('commit_game', args=[str(self.game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test game points for player 0
        url = reverse('v2-game-points', kwargs={'player_uuid': self.players[0].player_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data['points']), 1)  # One game
        game_data = data['points'][0]
        
        # Check game details
        self.assertEqual(game_data['total_rounds'], 2)
        self.assertEqual(game_data['solo_count'], 1)
        self.assertEqual(game_data['points'], 11)  # 2 from normal + 9 from solo

    def test_round_points(self):
        """Test round points endpoint."""
        # First add a round that causes a bock
        self.add_normal_round(
            winners=[self.players[0], self.players[1]],
            losers=[self.players[2], self.players[3]],
            points=2,
            bock_parallel=1  # This will set up a bock round
        )
        
        # Now add a round during bock (points will be doubled)
        self.add_normal_round(
            winners=[self.players[2], self.players[3]],
            losers=[self.players[0], self.players[1]],
            points=1  # This will become -2 due to bock multiplier
        )
        
        # Add a solo round
        self.add_solo_round(
            winner=self.players[0],
            losers=[self.players[1], self.players[2], self.players[3]],
            points=3
        )

        # Test round points for player 0
        url = reverse('v2-round-points', kwargs={'player_uuid': self.players[0].player_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data['points']), 3)  # Three rounds
        
        # Verify round details
        rounds = sorted(data['points'], key=lambda x: x['points'])
        
        # Lost bock round (-2)
        self.assertEqual(rounds[0]['points'], -2)
        self.assertEqual(rounds[0]['bock_multiplier'], 2)
        self.assertFalse(rounds[0]['was_solo'])
        
        # Won normal round (+2)
        self.assertEqual(rounds[1]['points'], 2)
        self.assertEqual(rounds[1]['bock_multiplier'], 1)
        self.assertFalse(rounds[1]['was_solo'])
        
        # Won solo round (+18 = 3 points * 3 for solo * 2 for bock)
        # The bock multiplier is still 2 because the bock round hasn't ended (takes 4 rounds)
        self.assertEqual(rounds[2]['points'], 18)
        self.assertEqual(rounds[2]['bock_multiplier'], 2)
        self.assertTrue(rounds[2]['was_solo'])

    def test_round_points_filtering(self):
        """Test round points filtering options."""
        # Add various rounds
        self.add_normal_round(
            winners=[self.players[0], self.players[1]],
            losers=[self.players[2], self.players[3]],
            points=2
        )
        
        self.add_solo_round(
            winner=self.players[0],
            losers=[self.players[1], self.players[2], self.players[3]],
            points=3
        )

        url = reverse('v2-round-points', kwargs={'player_uuid': self.players[0].player_id})
        
        # Test game type filter
        response = self.client.get(f"{url}?game_type=solo")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['points']), 1)
        self.assertTrue(data['points'][0]['was_solo'])
        
        response = self.client.get(f"{url}?game_type=normal")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['points']), 1)
        self.assertFalse(data['points'][0]['was_solo'])

    def test_deprecated_endpoint(self):
        """Test that old endpoint returns deprecation warning."""
        url = reverse('v2-filtered-player-points', kwargs={'player_uuid': self.players[0].player_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertIn('warning', response.json())
        self.assertIn('deprecated', response.json()['warning'].lower())