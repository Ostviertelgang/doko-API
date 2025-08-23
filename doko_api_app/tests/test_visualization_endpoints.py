from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from doko_api_app.models import Game, Player, Round, PlayerPoints
from PIL import Image
import io


class TestVisualizationEndpoints(TestCase):
    def setUp(self):
        # Create test user and authenticate
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test players
        self.test_players = [Player.objects.create(name=f'Test Player {i}') for i in range(4)]
        
        # Create test game
        data = {
            'game_name': 'Test Game',
            'players': [player.player_id for player in self.test_players]
        }
        response = self.client.post(reverse('game-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.game = Game.objects.get(game_id=response.data['game_id'])
        
        # Create test rounds with points
        self.create_test_rounds()
    
    def create_test_rounds(self):
        """Create test rounds with known point values"""
        # Round 1: Player 1 & 2 win, Player 3 & 4 lose
        round1 = Round.objects.create(game=self.game)
        pp1 = PlayerPoints.objects.create(player=self.test_players[0], points=40)
        pp2 = PlayerPoints.objects.create(player=self.test_players[1], points=40)
        pp3 = PlayerPoints.objects.create(player=self.test_players[2], points=-40)
        pp4 = PlayerPoints.objects.create(player=self.test_players[3], points=-40)
        round1.player_points.add(pp1, pp2, pp3, pp4)
        
        # Round 2: Player 1 & 3 win, Player 2 & 4 lose
        round2 = Round.objects.create(game=self.game)
        pp5 = PlayerPoints.objects.create(player=self.test_players[0], points=30)
        pp6 = PlayerPoints.objects.create(player=self.test_players[1], points=-30)
        pp7 = PlayerPoints.objects.create(player=self.test_players[2], points=30)
        pp8 = PlayerPoints.objects.create(player=self.test_players[3], points=-30)
        round2.player_points.add(pp5, pp6, pp7, pp8)
    
    def test_get_points_progression_gif(self):
        """Test getting points progression GIF"""
        url = reverse('points-progression-gif', args=[str(self.game.game_id)])
        
        # Test with default duration
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'image/gif')
        
        # Verify it's a valid GIF
        image = Image.open(io.BytesIO(response.content))
        self.assertEqual(image.format, 'GIF')
        self.assertTrue(getattr(image, 'is_animated', False))
        image.close()
        
        # Test with custom duration
        response = self.client.get(f"{url}?duration=1000")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'image/gif')
    
    def test_get_points_progression_image(self):
        """Test getting points progression static image"""
        url = reverse('points-progression-image', args=[str(self.game.game_id)])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'image/png')
        
        # Verify it's a valid PNG
        image = Image.open(io.BytesIO(response.content))
        self.assertEqual(image.format, 'PNG')
        image.close()
    
    def test_invalid_game_id(self):
        """Test endpoints with invalid game ID"""
        invalid_id = '00000000-0000-0000-0000-000000000000'
        
        # Test GIF endpoint
        url = reverse('points-progression-gif', args=[invalid_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'Game not found.'})
        
        # Test static image endpoint
        url = reverse('points-progression-image', args=[invalid_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'error': 'Game not found.'})
    
    def test_invalid_duration(self):
        """Test GIF endpoint with invalid duration parameter"""
        url = reverse('points-progression-gif', args=[str(self.game.game_id)])
        
        # Test negative duration
        response = self.client.get(f"{url}?duration=-1")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'Duration must be a positive number'})
        
        # Test non-numeric duration
        response = self.client.get(f"{url}?duration=invalid")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'Invalid duration parameter'})
    
    def test_game_with_no_players(self):
        """Test visualization for game with no players"""
        # Create empty game
        empty_game = Game.objects.create(game_name="Empty Game")
        
        # Test GIF endpoint
        url = reverse('points-progression-gif', args=[str(empty_game.game_id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'Game has no players'})
        
        # Test static image endpoint
        url = reverse('points-progression-image', args=[str(empty_game.game_id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'Game has no players'})
    
    def test_authentication_required(self):
        """Test that endpoints require authentication"""
        # Create unauthenticated client
        client = APIClient()
        
        # Test GIF endpoint
        url = reverse('points-progression-gif', args=[str(self.game.game_id)])
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test static image endpoint
        url = reverse('points-progression-image', args=[str(self.game.game_id)])
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_points_accumulation(self):
        """Test that points are correctly accumulated in visualizations"""
        # Get static image to verify points
        url = reverse('points-progression-image', args=[str(self.game.game_id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify points through the rounds endpoint
        response = self.client.get(reverse('get_all_rounds', args=[str(self.game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rounds = response.json()
        
        # Verify first round points
        first_round = rounds[0]
        for player_points in first_round['player_points']:
            if player_points['player'] == str(self.test_players[0].player_id):
                self.assertEqual(player_points['points'], 40)
            elif player_points['player'] == str(self.test_players[1].player_id):
                self.assertEqual(player_points['points'], 40)
            elif player_points['player'] == str(self.test_players[2].player_id):
                self.assertEqual(player_points['points'], -40)
            elif player_points['player'] == str(self.test_players[3].player_id):
                self.assertEqual(player_points['points'], -40)
        
        # Verify second round points
        second_round = rounds[1]
        for player_points in second_round['player_points']:
            if player_points['player'] == str(self.test_players[0].player_id):
                self.assertEqual(player_points['points'], 30)
            elif player_points['player'] == str(self.test_players[1].player_id):
                self.assertEqual(player_points['points'], -30)
            elif player_points['player'] == str(self.test_players[2].player_id):
                self.assertEqual(player_points['points'], 30)
            elif player_points['player'] == str(self.test_players[3].player_id):
                self.assertEqual(player_points['points'], -30)