import json
import uuid
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient

from doko_api_app.models import Game, Round, Player, PlayerPoints

class StatsEndpointsTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create client and login
        self.client = APIClient()
        self.client.login(username='testuser', password='testpassword')
        
        # Create test players
        self.player1 = Player.objects.create(name='Player 1')
        self.player2 = Player.objects.create(name='Player 2')
        self.player3 = Player.objects.create(name='Player 3')
        self.player4 = Player.objects.create(name='Player 4')
        
        # Create a game
        self.game = Game.objects.create(
            game_name='Test Game',
            is_closed=False
        )
        self.game.players.add(self.player1, self.player2, self.player3, self.player4)
        
        # Create player points
        self.pp1 = PlayerPoints.objects.create(player=self.player1, points=30)
        self.pp2 = PlayerPoints.objects.create(player=self.player2, points=30)
        self.pp3 = PlayerPoints.objects.create(player=self.player3, points=-30)
        self.pp4 = PlayerPoints.objects.create(player=self.player4, points=-30)
        
        # Create a round
        self.round1 = Round.objects.create(
            game=self.game,
            points=30,
            bock_multiplier=1
        )
        self.round1.player_points.add(self.pp1, self.pp2, self.pp3, self.pp4)
        
        # Create a solo round
        self.pp5 = PlayerPoints.objects.create(player=self.player1, points=90)
        self.pp6 = PlayerPoints.objects.create(player=self.player2, points=-30)
        self.pp7 = PlayerPoints.objects.create(player=self.player3, points=-30)
        self.pp8 = PlayerPoints.objects.create(player=self.player4, points=-30)
        
        self.round2 = Round.objects.create(
            game=self.game,
            points=90,
            bock_multiplier=1,
            was_solo_by=self.player1
        )
        self.round2.player_points.add(self.pp5, self.pp6, self.pp7, self.pp8)
        
        # Add player points to game
        self.game.player_points.add(self.pp1, self.pp2, self.pp3, self.pp4, self.pp5, self.pp6, self.pp7, self.pp8)
        
        # Get JWT token for authenticated requests
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'testuser', 'password': 'testpassword'},
            format='json'
        )
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_get_player_best_rounds(self):
        """Test the best rounds endpoint"""
        url = reverse('stats-player-best-rounds', args=[self.player1.player_id])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('best_rounds', data)
        self.assertEqual(len(data['best_rounds']), 2)  # Player 1 has 2 rounds
        
        # Check sorting - solo round should be first (more points)
        best_round = data['best_rounds'][0]
        self.assertEqual(best_round['points'], 90)
        self.assertEqual(best_round['game_type'], 'solo')
        
        # Verify math and data integrity
        normal_round = data['best_rounds'][1]
        self.assertEqual(normal_round['points'], 30)
        self.assertEqual(normal_round['game_type'], 'normal')
        self.assertEqual(normal_round['bock_multiplier'], 1)
        
        # Check that the round is associated with the correct game
        self.assertEqual(str(best_round['game_id']), str(self.game.game_id))

    def test_get_leaderboard(self):
        """Test the leaderboard endpoint"""
        url = reverse('stats-leaderboard')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('leaderboard', data)
        
        # Player 1 should be at the top with most points
        top_player = data['leaderboard'][0]
        self.assertEqual(top_player['player_name'], 'Player 1')
        
        # Verify the math for Player 1 (120 total points from 2 rounds)
        self.assertEqual(top_player['total_points'], 120)  # 30 from normal + 90 from solo
        self.assertEqual(top_player['games_played'], 1)
        self.assertEqual(top_player['win_rate'], 1.0)  # Won 2 out of 2 rounds
        self.assertEqual(top_player['avg_points_per_game'], 120.0)  # 120 points / 1 game
        
        # Test with different metrics
        response = self.client.get(f"{url}?metric=win_rate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get(f"{url}?metric=avg_points_per_game")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_player_win_loss(self):
        """Test the win/loss analysis endpoint"""
        url = reverse('stats-player-win-loss', args=[self.player1.player_id])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('summary', data)
        self.assertIn('by_game_type', data)
        
        # Player 1 should have 2 wins
        self.assertEqual(data['summary']['wins'], 2)
        self.assertEqual(data['summary']['losses'], 0)
        self.assertEqual(data['summary']['rounds_played'], 2)
        self.assertEqual(data['summary']['games_played'], 1)
        
        # Check the win rate calculation (2 wins out of 2 rounds = 100%)
        self.assertEqual(data['summary']['win_rate'], 1.0)
        
        # Verify average points calculation (30 + 90) / 2 = 60
        self.assertEqual(data['summary']['average_points_per_round'], 60.0)
        
        # Check game type breakdown
        self.assertEqual(data['by_game_type']['normal']['wins'], 1)
        self.assertEqual(data['by_game_type']['normal']['losses'], 0)
        self.assertEqual(data['by_game_type']['normal']['rounds_played'], 1)
        self.assertEqual(data['by_game_type']['normal']['win_rate'], 1.0)
        
        self.assertEqual(data['by_game_type']['solo']['wins'], 1)
        self.assertEqual(data['by_game_type']['solo']['losses'], 0)
        self.assertEqual(data['by_game_type']['solo']['rounds_played'], 1)
        self.assertEqual(data['by_game_type']['solo']['win_rate'], 1.0)
        
        # Check pflichtsolo section exists (should be 0 rounds)
        self.assertEqual(data['by_game_type']['pflichtsolo']['rounds_played'], 0)

    def test_get_game_type_performance(self):
        """Test the game type performance endpoint"""
        url = reverse('stats-player-game-type-performance', args=[self.player1.player_id])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('by_game_type', data)
        
        # Player 1 should have normal and solo game stats
        self.assertIn('normal', data['by_game_type'])
        self.assertIn('solo', data['by_game_type'])
        
        # Verify normal game stats
        self.assertEqual(data['by_game_type']['normal']['rounds_played'], 1)
        self.assertEqual(data['by_game_type']['normal']['win_rate'], 1.0)
        self.assertEqual(data['by_game_type']['normal']['average_points'], 30.0)
        self.assertEqual(data['by_game_type']['normal']['best_round']['points'], 30)
        
        # Verify solo game stats
        self.assertEqual(data['by_game_type']['solo']['rounds_played'], 1)
        self.assertEqual(data['by_game_type']['solo']['win_rate'], 1.0)
        self.assertEqual(data['by_game_type']['solo']['average_points'], 90.0)
        self.assertEqual(data['by_game_type']['solo']['best_round']['points'], 90)
        
        # Solo should have higher average points
        solo_avg = data['by_game_type']['solo']['average_points']
        normal_avg = data['by_game_type']['normal']['average_points']
        self.assertGreater(solo_avg, normal_avg)
        self.assertEqual(solo_avg, 90.0)
        self.assertEqual(normal_avg, 30.0)

    def test_get_player_trends(self):
        """Test the player trends endpoint"""
        url = reverse('stats-player-trends', args=[self.player1.player_id])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('data', data)
        self.assertIn('trend_analysis', data)
        
        # Check if there's at least one data point
        self.assertTrue(len(data['data']) > 0)
        
        # Verify that points for the period match our test data
        # The default metric is 'points'
        total_points = 0
        for period_data in data['data']:
            total_points += period_data['value']
        
        # Total points should equal the sum of all Player 1's points (30 + 90 = 120)
        self.assertEqual(total_points, 120)
        
        # Test with different parameters
        response = self.client.get(f"{url}?metric=win_rate&interval=week")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # For win_rate, values should be between 0 and 1
        win_rate_data = response.data['data']
        for period_data in win_rate_data:
            if period_data['games_played'] > 0:  # Only check periods with games
                self.assertGreaterEqual(period_data['value'], 0.0)
                self.assertLessEqual(period_data['value'], 1.0)

    def test_invalid_player_id(self):
        """Test endpoints with invalid player ID"""
        fake_uuid = uuid.uuid4()
        
        # Best rounds
        url = reverse('stats-player-best-rounds', args=[fake_uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Win/loss
        url = reverse('stats-player-win-loss', args=[fake_uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Game type performance
        url = reverse('stats-player-game-type-performance', args=[fake_uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Trends
        url = reverse('stats-player-trends', args=[fake_uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_parameters(self):
        """Test endpoints with invalid query parameters"""
        # Best rounds with invalid limit
        url = reverse('stats-player-best-rounds', args=[self.player1.player_id])
        response = self.client.get(f"{url}?limit=invalid")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Leaderboard with invalid metric
        url = reverse('stats-leaderboard')
        response = self.client.get(f"{url}?metric=invalid_metric")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Trends with invalid interval
        url = reverse('stats-player-trends', args=[self.player1.player_id])
        response = self.client.get(f"{url}?interval=invalid_interval")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)