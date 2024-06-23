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

    def test_add_round_normal(self):
        """Test the /games/<game_id>/add_round/ endpoint with a normal round."""
        data = {
            'winning_players': [str(self.test_players[0].player_id), str(self.test_players[1].player_id)],
            'losing_players': [str(self.test_players[2].player_id), str(self.test_players[3].player_id)],
            'points': 10,
            'caused_bock_parrallel': 0,
        }
        response = self.client.post(reverse('add_round', args=[str(self.test_game.game_id)]), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Round.objects.count(), 1)
        self.assertEqual(PlayerPoints.objects.count(), 4)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[0]).points, 10)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[1]).points, 10)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[2]).points, -10)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[3]).points, -10)

    def test_add_round_bock(self):
        """Test the /games/<game_id>/add_round/ endpoint with a bock round."""
        data = {
            'winning_players': [str(self.test_players[0].player_id), str(self.test_players[1].player_id)],
            'losing_players': [str(self.test_players[2].player_id), str(self.test_players[3].player_id)],
            'points': 10,
            'caused_bock_parrallel': 1,
        }
        response = self.client.post(reverse('add_round', args=[str(self.test_game.game_id)]), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Round.objects.count(), 1)
        self.assertEqual(PlayerPoints.objects.count(), 4)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[0]).points, 10)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[1]).points, 10)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[2]).points, -10)
        self.assertEqual(PlayerPoints.objects.get(player=self.test_players[3]).points, -10)
        # get the bock status
        response = self.client.get(reverse('get_bock_status', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bock_round_status'], [4])
        # play a round causing a double bock
        data = {
            'winning_players': [str(self.test_players[0].player_id), str(self.test_players[1].player_id)],
            'losing_players': [str(self.test_players[2].player_id), str(self.test_players[3].player_id)],
            'points': 10,
            'caused_bock_parrallel': 2,
        }
        response = self.client.post(reverse('add_round', args=[str(self.test_game.game_id)]), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Round.objects.count(), 2)
        self.assertEqual(PlayerPoints.objects.count(), 8)
        # use the /games/<game_id>/rounds/ endpoint to get the points
        response = self.client.get(reverse('get_all_rounds', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the last round
        last_round = response.data[-1]

        # Now you can access the data of the last round
        for player_points in last_round['player_points']:
            if player_points['player'] == str(self.test_players[0].player_id):
                self.assertEqual(player_points['points'], 20)
            elif player_points['player'] == str(self.test_players[1].player_id):
                self.assertEqual(player_points['points'], 20)
            elif player_points['player'] == str(self.test_players[2].player_id):
                self.assertEqual(player_points['points'], -20)
            elif player_points['player'] == str(self.test_players[3].player_id):
                self.assertEqual(player_points['points'], -20)
        # get the bock status
        response = self.client.get(reverse('get_bock_status', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bock_round_status'], [3, 4, 4])

        # add a new round
        data = {
            'winning_players': [str(self.test_players[0].player_id), str(self.test_players[1].player_id)],
            'losing_players': [str(self.test_players[2].player_id), str(self.test_players[3].player_id)],
            'points': 10,
            'caused_bock_parrallel': 0,
        }
        response = self.client.post(reverse('add_round', args=[str(self.test_game.game_id)]), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Round.objects.count(), 3)
        self.assertEqual(PlayerPoints.objects.count(), 12)

        # use the /games/<game_id>/rounds/ endpoint to get the points
        response = self.client.get(reverse('get_all_rounds', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the last round
        last_round = response.data[-1]
        for player_points in last_round['player_points']:
            if player_points['player'] == str(self.test_players[0].player_id):
                self.assertEqual(player_points['points'], 80)
            elif player_points['player'] == str(self.test_players[1].player_id):
                self.assertEqual(player_points['points'], 80)
            elif player_points['player'] == str(self.test_players[2].player_id):
                self.assertEqual(player_points['points'], -80)
            elif player_points['player'] == str(self.test_players[3].player_id):
                self.assertEqual(player_points['points'], -80)

        # get the bock status
        response = self.client.get(reverse('get_bock_status', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bock_round_status'], [2, 3, 3])


    def test_get_players_with_pflichtsolo(self):
        """Test the /games/<game_id>/get_pflichtsolo/ endpoint."""
        # add a round with a pflichtsolo
        data = {
            'winning_players': [str(self.test_players[0].player_id)],
            'losing_players': [str(self.test_players[2].player_id), str(self.test_players[3].player_id), str(self.test_players[1].player_id)],
            'points': 10,
            'caused_bock_parrallel': 0
        }
        response = self.client.post(reverse('add_round', args=[str(self.test_game.game_id)]), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Round.objects.count(), 1)
        self.assertEqual(PlayerPoints.objects.count(), 4)
        # get the players with pflichtsolo
        response = self.client.get(reverse('get_pflichtsolo', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual({player['player_id'] for player in response.data}, {str(player.player_id) for player in [self.test_players[1], self.test_players[2], self.test_players[3] ]})
        # check the poitns
        response = self.client.get(reverse('get_all_rounds', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the last round
        last_round = response.data[-1]
        for player_points in last_round['player_points']:
            if player_points['player'] == str(self.test_players[0].player_id):
                self.assertEqual(player_points['points'], 30)
            elif player_points['player'] == str(self.test_players[1].player_id):
                self.assertEqual(player_points['points'], -10)
            elif player_points['player'] == str(self.test_players[2].player_id):
                self.assertEqual(player_points['points'], -10)
            elif player_points['player'] == str(self.test_players[3].player_id):
                self.assertEqual(player_points['points'], -10)

        # player 1 looses his solo
        data = {
            'winning_players': [str(self.test_players[1].player_id)],
            'losing_players': [str(self.test_players[2].player_id), str(self.test_players[3].player_id), str(self.test_players[0].player_id)],
            'points': -10,
            'caused_bock_parrallel': 0,
        }
        response = self.client.post(reverse('add_round', args=[str(self.test_game.game_id)]), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # get the players with pflichtsolo
        response = self.client.get(reverse('get_pflichtsolo', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({player['player_id'] for player in response.data}, {str(player.player_id) for player in [self.test_players[2], self.test_players[3]]})

        # check the points via get_rounds endpoint
        response = self.client.get(reverse('get_all_rounds', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the last round
        last_round = response.data[-1]
        for player_points in last_round['player_points']:
            if player_points['player'] == str(self.test_players[0].player_id):
                self.assertEqual(player_points['points'], 10)
            elif player_points['player'] == str(self.test_players[1].player_id):
                self.assertEqual(player_points['points'], -30)
            elif player_points['player'] == str(self.test_players[2].player_id):
                self.assertEqual(player_points['points'], 10)
            elif player_points['player'] == str(self.test_players[3].player_id):
                self.assertEqual(player_points['points'], 10)

    def test_undo_round(self):
        """Test the /games/<game_id>/undo_round/ endpoint."""
        # add a round
        data = {
            'winning_players': [str(self.test_players[0].player_id), str(self.test_players[1].player_id)],
            'losing_players': [str(self.test_players[2].player_id), str(self.test_players[3].player_id)],
            'points': 10,
            'caused_bock_parrallel': 0,
        }
        response = self.client.post(reverse('add_round', args=[str(self.test_game.game_id)]), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Round.objects.count(), 1)
        self.assertEqual(PlayerPoints.objects.count(), 4)
        # check the points via get_rounds endpoint
        response = self.client.get(reverse('get_all_rounds', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the last round
        last_round = response.data[-1]
        for player_points in last_round['player_points']:
            if player_points['player'] == str(self.test_players[0].player_id):
                self.assertEqual(player_points['points'], 10)
            elif player_points['player'] == str(self.test_players[1].player_id):
                self.assertEqual(player_points['points'], 10)
            elif player_points['player'] == str(self.test_players[2].player_id):
                self.assertEqual(player_points['points'], -10)
            elif player_points['player'] == str(self.test_players[3].player_id):
                self.assertEqual(player_points['points'], -10)

        # undo the round
        response = self.client.post(reverse('undo_round', args=[str(self.test_game.game_id)]), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Round.objects.count(), 0)
        self.assertEqual(PlayerPoints.objects.count(), 0)
        # check the points via get_rounds endpoint
        response = self.client.get(reverse('get_all_rounds', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # make a bockrunde and undo it
        data = {
            'winning_players': [str(self.test_players[0].player_id), str(self.test_players[1].player_id)],
            'losing_players': [str(self.test_players[2].player_id), str(self.test_players[3].player_id)],
            'points': 10,
            'caused_bock_parrallel': 1,
        }
        response = self.client.post(reverse('add_round', args=[str(self.test_game.game_id)]), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Round.objects.count(), 1)
        self.assertEqual(PlayerPoints.objects.count(), 4)
        # check the points via get_rounds endpoint
        response = self.client.get(reverse('get_all_rounds', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the last round
        last_round = response.data[-1]
        for player_points in last_round['player_points']:
            if player_points['player'] == str(self.test_players[0].player_id):
                self.assertEqual(player_points['points'], 10)
            elif player_points['player'] == str(self.test_players[1].player_id):
                self.assertEqual(player_points['points'], 10)
            elif player_points['player'] == str(self.test_players[2].player_id):
                self.assertEqual(player_points['points'], -10)
            elif player_points['player'] == str(self.test_players[3].player_id):
                self.assertEqual(player_points['points'], -10)
        # undo the round
        response = self.client.post(reverse('undo_round', args=[str(self.test_game.game_id)]), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Round.objects.count(), 0)
        self.assertEqual(PlayerPoints.objects.count(), 0)
        # check the points via get_rounds endpoint
        response = self.client.get(reverse('get_all_rounds', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        # get the bock status
        response = self.client.get(reverse('get_bock_status', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bock_round_status'], [])

        # make doppelbock, then single bock with solo,check points and solo and bock status ,undo the last round recheck
        data = {
            'winning_players': [str(self.test_players[0].player_id), str(self.test_players[1].player_id)],
            'losing_players': [str(self.test_players[2].player_id), str(self.test_players[3].player_id)],
            'points': 10,
            'caused_bock_parrallel': 2,
        }
        response = self.client.post(reverse('add_round', args=[str(self.test_game.game_id)]), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Round.objects.count(), 1)
        self.assertEqual(PlayerPoints.objects.count(), 4)

        data = {
            'winning_players': [str(self.test_players[0].player_id)],
            'losing_players': [str(self.test_players[2].player_id), str(self.test_players[3].player_id), str(self.test_players[1].player_id)],
            'points': 10,
            'caused_bock_parrallel': 1,
        }
        response = self.client.post(reverse('add_round', args=[str(self.test_game.game_id)]), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Round.objects.count(), 2)
        self.assertEqual(PlayerPoints.objects.count(), 8)
        # check the points via get_rounds endpoint
        response = self.client.get(reverse('get_all_rounds', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the last round
        last_round = response.data[-1]
        for player_points in last_round['player_points']:
            if player_points['player'] == str(self.test_players[0].player_id):
                self.assertEqual(player_points['points'], 60)
            elif player_points['player'] == str(self.test_players[1].player_id):
                self.assertEqual(player_points['points'], -20)
            elif player_points['player'] == str(self.test_players[2].player_id):
                self.assertEqual(player_points['points'], -20)
            elif player_points['player'] == str(self.test_players[3].player_id):
                self.assertEqual(player_points['points'], -20)

        # get the bock status
        response = self.client.get(reverse('get_bock_status', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bock_round_status'], [3,3,4])
        # get pflichtsolo
        response = self.client.get(reverse('get_pflichtsolo', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        # check player0 played pflichtsolo
        self.assertEqual({player['player_id'] for player in response.data}, {str(player.player_id) for player in [self.test_players[1], self.test_players[2], self.test_players[3] ]})

        # undo the round
        response = self.client.post(reverse('undo_round', args=[str(self.test_game.game_id)]), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Round.objects.count(), 1)
        self.assertEqual(PlayerPoints.objects.count(), 4)
        # check the points via get_rounds endpoint
        response = self.client.get(reverse('get_all_rounds', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the last round
        last_round = response.data[-1]
        for player_points in last_round['player_points']:
            if player_points['player'] == str(self.test_players[0].player_id):
                self.assertEqual(player_points['points'], 10)
            elif player_points['player'] == str(self.test_players[1].player_id):
                self.assertEqual(player_points['points'], 10)
            elif player_points['player'] == str(self.test_players[2].player_id):
                self.assertEqual(player_points['points'], -10)
            elif player_points['player'] == str(self.test_players[3].player_id):
                self.assertEqual(player_points['points'], -10)
        # get the bock status
        response = self.client.get(reverse('get_bock_status', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bock_round_status'], [4,4])
        # get pflichtsolo
        response = self.client.get(reverse('get_pflichtsolo', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        # undo the round
        response = self.client.post(reverse('undo_round', args=[str(self.test_game.game_id)]), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Round.objects.count(), 0)
        self.assertEqual(PlayerPoints.objects.count(), 0)
        # check the points via get_rounds endpoint
        response = self.client.get(reverse('get_all_rounds', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        # get the bock status
        response = self.client.get(reverse('get_bock_status', args=[str(self.test_game.game_id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bock_round_status'], [])



