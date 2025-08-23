from matplotlib import pyplot as plt
import io
from PIL import Image
import numpy as np
from datetime import datetime
from typing import Tuple, Dict, List, Any, Optional


class PointsVisualizer:
    def __init__(self, game):
        """
        Initialize the visualizer with a game instance
        
        Args:
            game: Game model instance
            
        Raises:
            ValueError: If game has no players
        """
        self.game = game
        self.rounds = game.get_all_rounds().order_by('created_at')
        self.players = game.players.all()
        
        if not self.players.exists():
            raise ValueError("Game has no players")
        
        # Fixed figure dimensions for consistent output
        self.fig_width = 10
        self.fig_height = 6
    
    def _prepare_data(self) -> Tuple[List[int], Dict[str, Dict[str, Any]]]:
        """
        Prepare points progression data for visualization
        
        Returns:
            tuple: (round_numbers, player_points)
                - round_numbers: list of round numbers including 0
                - player_points: dict of player data including name and points progression
                
        Raises:
            ValueError: If there's an issue with the data
        """
        try:
            player_points = {
                player.player_id: {
                    'name': player.name,
                    'points': [0]  # Start with 0 points
                } for player in self.players
            }
            round_numbers = [0]  # Start with round 0
            
            for round_num, round_obj in enumerate(self.rounds, 1):
                round_numbers.append(round_num)
                
                # Update points for each player
                for player_id in player_points:
                    current_points = player_points[player_id]['points'][-1]  # Get last point value
                    round_points = sum(
                        pp.points for pp in round_obj.player_points.all() 
                        if pp.player.player_id == player_id
                    )
                    player_points[player_id]['points'].append(current_points + round_points)
            
            return round_numbers, player_points
            
        except Exception as e:
            raise ValueError(f"Error preparing data: {str(e)}")
    
    def _get_axis_limits(self, round_numbers: List[int], player_points: Dict[str, Dict[str, Any]]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Determine the axis limits from the complete dataset
        
        Args:
            round_numbers: List of round numbers
            player_points: Dictionary of player data
            
        Returns:
            tuple: ((xmin, xmax), (ymin, ymax))
        """
        # Create temporary figure to determine limits
        fig = plt.figure(figsize=(self.fig_width, self.fig_height))
        
        try:
            # Plot complete data for all players
            for player_data in player_points.values():
                plt.plot(round_numbers, player_data['points'])
            
            # Get current axis limits
            ax = plt.gca()
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            
            return xlim, ylim
        finally:
            plt.close(fig)

    def _create_figure(self, round_numbers: List[int], player_points: Dict[str, Dict[str, Any]],
                      current_round: int, axis_limits: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None) -> bytes:
        """
        Create a figure for a specific round
        
        Args:
            round_numbers: List of round numbers
            player_points: Dictionary of player data
            current_round: The current round to visualize up to
            axis_limits: Optional fixed axis limits ((xmin, xmax), (ymin, ymax))
            
        Returns:
            bytes: The rendered figure as PNG bytes
        """
        fig = plt.figure(figsize=(self.fig_width, self.fig_height))
        
        try:
            # Plot each player's points up to current round
            for player_data in player_points.values():
                plt.plot(
                    round_numbers[:current_round+1],
                    player_data['points'][:current_round+1],
                    marker='o',
                    label=player_data['name'],
                    linewidth=2,
                    markersize=8
                )
            
            plt.title(f'Points Progression - Round {current_round}', fontsize=14, pad=20)
            plt.xlabel('Round', fontsize=12)
            plt.ylabel('Points', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # Set fixed axis limits if provided
            if axis_limits:
                xlim, ylim = axis_limits
                plt.xlim(xlim)
                plt.ylim(ylim)
            
            # Add some padding to the layout
            plt.tight_layout()
            
            # Convert plot to PNG bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            return buf.getvalue()
            
        finally:
            plt.close(fig)
            buf.close()
    
    def create_gif(self, duration_ms: int = 500) -> io.BytesIO:
        """
        Create animated GIF of points progression
        
        Args:
            duration_ms: Duration of each frame in milliseconds
            
        Returns:
            BytesIO: GIF image data
            
        Raises:
            ValueError: If duration is invalid or there's an error creating the GIF
        """
        if not isinstance(duration_ms, (int, float)) or duration_ms <= 0:
            raise ValueError("Duration must be a positive number")
        
        try:
            round_numbers, player_points = self._prepare_data()
            frames = []
            
            # Get axis limits from complete dataset
            axis_limits = self._get_axis_limits(round_numbers, player_points)
            
            # Create a frame for each round with fixed axis limits
            for i in range(len(round_numbers)):
                png_data = self._create_figure(round_numbers, player_points, i, axis_limits)
                image = Image.open(io.BytesIO(png_data))
                frames.append(image.convert('P'))  # Convert to palette mode for GIF
            
            # Save as animated GIF
            output = io.BytesIO()
            if frames:
                frames[0].save(
                    output,
                    format='GIF',
                    save_all=True,
                    append_images=frames[1:],
                    duration=duration_ms,
                    loop=0,
                    optimize=False
                )
                output.seek(0)
                return output
            else:
                raise ValueError("No frames generated for GIF")
                
        except Exception as e:
            raise ValueError(f"Error creating GIF: {str(e)}")
    
    def create_static_image(self) -> io.BytesIO:
        """
        Create static image of final points progression
        
        Returns:
            BytesIO: PNG image data
            
        Raises:
            ValueError: If there's an error creating the image
        """
        try:
            round_numbers, player_points = self._prepare_data()
            
            # Create the final figure
            png_data = self._create_figure(round_numbers, player_points, len(round_numbers)-1)
            
            # Return as BytesIO
            output = io.BytesIO(png_data)
            return output
            
        except Exception as e:
            raise ValueError(f"Error creating static image: {str(e)}")
