import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, call
from PIL import Image
import io
import matplotlib.pyplot as plt
from django.test import TestCase
from doko_api_app.models import Game, Round, PlayerPoints, Player
from doko_api_app.points_visualization import PointsVisualizer

class TestPointsVisualizer(TestCase):
    def setUp(self):
        # Create test players
        self.player1 = Player.objects.create(name="Player 1")
        self.player2 = Player.objects.create(name="Player 2")
        self.player3 = Player.objects.create(name="Player 3")
        self.player4 = Player.objects.create(name="Player 4")
        
        # Create a test game
        self.game = Game.objects.create(game_name="Test Game")
        self.game.players.add(self.player1, self.player2, self.player3, self.player4)
        
        # Create test rounds with points
        self.create_test_rounds()
        
        self.visualizer = PointsVisualizer(self.game)
    
    def create_test_rounds(self):
        """Create a series of test rounds with known point values"""
        # Round 1: Player 1 & 2 win, Player 3 & 4 lose
        round1 = Round.objects.create(game=self.game)
        pp1 = PlayerPoints.objects.create(player=self.player1, points=40)
        pp2 = PlayerPoints.objects.create(player=self.player2, points=40)
        pp3 = PlayerPoints.objects.create(player=self.player3, points=-40)
        pp4 = PlayerPoints.objects.create(player=self.player4, points=-40)
        round1.player_points.add(pp1, pp2, pp3, pp4)
        
        # Round 2: Player 1 & 3 win, Player 2 & 4 lose
        round2 = Round.objects.create(game=self.game)
        pp5 = PlayerPoints.objects.create(player=self.player1, points=30)
        pp6 = PlayerPoints.objects.create(player=self.player2, points=-30)
        pp7 = PlayerPoints.objects.create(player=self.player3, points=30)
        pp8 = PlayerPoints.objects.create(player=self.player4, points=-30)
        round2.player_points.add(pp5, pp6, pp7, pp8)
    
    def test_prepare_data_empty_game(self):
        """Test _prepare_data with a game that has no rounds"""
        empty_game = Game.objects.create(game_name="Empty Game")
        empty_game.players.add(self.player1, self.player2)
        visualizer = PointsVisualizer(empty_game)
        
        round_numbers, player_points = visualizer._prepare_data()
        
        self.assertEqual(round_numbers, [0])
        self.assertEqual(len(player_points), 2)
        for player_data in player_points.values():
            self.assertEqual(player_data['points'], [0])
    
    def test_prepare_data_accumulation(self):
        """Test that points are correctly accumulated over rounds"""
        round_numbers, player_points = self.visualizer._prepare_data()
        
        # Check round numbers
        self.assertEqual(round_numbers, [0, 1, 2])
        
        # Check point accumulation for each player
        expected_points = {
            self.player1.player_id: [0, 40, 70],   # Wins both rounds
            self.player2.player_id: [0, 40, 10],   # Wins first, loses second
            self.player3.player_id: [0, -40, -10], # Loses first, wins second
            self.player4.player_id: [0, -40, -70]  # Loses both rounds
        }
        
        for player_id, points in expected_points.items():
            self.assertEqual(
                player_points[player_id]['points'],
                points,
                f"Points mismatch for player {player_id}"
            )
    
    def test_create_static_image(self):
        """Test static image generation"""
        image_data = self.visualizer.create_static_image()
        
        # Verify it's a valid PNG
        image = Image.open(image_data)
        self.assertEqual(image.format, 'PNG')
        
        # Clean up
        image.close()
        image_data.close()
    
    def test_create_gif(self):
        """Test GIF generation"""
        gif_data = self.visualizer.create_gif(duration_ms=500)
        
        # Verify it's a valid GIF
        image = Image.open(gif_data)
        self.assertEqual(image.format, 'GIF')
        
        # Verify it's animated
        self.assertTrue(getattr(image, 'is_animated', False))
        
        # Clean up
        image.close()
        gif_data.close()
    
    def test_invalid_duration(self):
        """Test handling of invalid duration parameter"""
        with self.assertRaises(ValueError):
            self.visualizer.create_gif(duration_ms=-1)
        
        with self.assertRaises(ValueError):
            self.visualizer.create_gif(duration_ms="invalid")
    
    def test_resource_cleanup(self):
        """Test that resources are properly cleaned up"""
        with patch('matplotlib.pyplot.close') as mock_close:
            self.visualizer.create_static_image()
            mock_close.assert_called()
    
    def test_figure_size(self):
        """Test that figures are created with correct size"""
        with patch('matplotlib.pyplot.figure') as mock_figure:
            # Create a mock return value
            mock_figure.return_value = plt.figure()
            
            self.visualizer.create_static_image()
            
            # Check if figure was called with correct figsize
            mock_figure.assert_has_calls([
                call(figsize=(self.visualizer.fig_width, self.visualizer.fig_height))
            ])
    
    def test_memory_management(self):
        """Test for memory leaks in image generation"""
        initial_figures = len(plt.get_fignums())
        
        # Generate multiple images
        for _ in range(5):
            image_data = self.visualizer.create_static_image()
            image_data.close()
            
            gif_data = self.visualizer.create_gif()
            gif_data.close()
        
        # Verify no figure leaks
        final_figures = len(plt.get_fignums())
        self.assertEqual(initial_figures, final_figures)
    
    def tearDown(self):
        # Clean up any remaining matplotlib figures
        plt.close('all')