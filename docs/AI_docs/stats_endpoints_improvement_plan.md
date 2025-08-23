# Stats Endpoints Improvement Plan

## Current State (v1)

All existing endpoints will remain unchanged:
1. `/players/{player_id}/game-stats/`
2. `/players/{player_id}/round-stats/`
3. `/games/{game_id}/points-progression-gif/`
4. `/games/{game_id}/points-progression-image/`

## New Endpoints (v2)

### 1. Player Summary Stats
```
GET /v2/players/{player-uuid}/summary-stats/
```

Returns aggregated statistics for a player:
```json
{
    "total_games": int,
    "total_rounds": int,
    "total_points": int,
    "average_points_per_game": float,
    "average_points_per_round": float,
    "highest_game_points": int,
    "lowest_game_points": int,
    "win_rate": float,
    "solo_games": int,
    "solo_win_rate": float,
    "average_position": float,
    "first_place_count": int,
    "last_place_count": int
}
```

### 2. Game Type Stats
```
GET /v2/players/{player-uuid}/game-type-stats/
```

Returns statistics broken down by game type:
```json
{
    "normal_games": {
        "count": int,
        "win_rate": float,
        "average_points": float,
        "total_points": int,
        "average_position": float
    },
    "solo_games": {
        "count": int,
        "win_rate": float,
        "average_points": float,
        "total_points": int
    },
    "pflichtsolo_games": {
        "count": int,
        "win_rate": float,
        "average_points": float,
        "total_points": int
    },
    "bock_rounds": {
        "count": int,
        "win_rate": float,
        "average_points": float,
        "total_points": int,
        "average_multiplier": float
    }
}
```

### 3. Player Points
```
GET /v2/players/{player-uuid}/player-points/
```

Returns all player points for a player:
```json
{
    "player_id": uuid,
    "player_name": str,
    "points": [
        {
            "game_id": uuid,
            "game_name": str,
            "points": int,
            "created_at": datetime,
            "closed_at": datetime,
            "total_rounds": int,
            "final_position": int,
            "solo_count": int
        }
    ],
    "aggregates": {
        "total_points": int,
        "average_points_per_game": float,
        "total_games": int,
        "win_rate": float
    }
}
```

### 4. Filtered Player Points
```
GET /v2/players/{player-uuid}/points/
```

Returns filtered player points with various query options:
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_filtered_player_points(request, player_id):
    """
    Get player points with comprehensive filtering
    
    Query Parameters:
    - start_date: Filter points after this date
    - end_date: Filter points before this date
    - game_id: Filter by specific game
    - game_type: Filter by game type (normal, solo, pflichtsolo)
    - is_game_closed: Filter by game status
    - sort_by: Sort field (points, date)
    - sort_order: asc or desc
    
    Returns:
    {
        "total_count": int,
        "points": [
            {
                "points_id": uuid,
                "game_id": uuid,
                "game_name": str,
                "points": int,
                "created_at": datetime,
                "is_from_round": bool,
                "is_from_game": bool,
                "was_solo": bool,
                "was_pflichtsolo": bool,
                "bock_multiplier": int
            }
        ],
        "aggregates": {
            "total_points": int,
            "average_points": float,
            "min_points": int,
            "max_points": int
        }
    }
    """
```

## Implementation Plan

1. Create new v2 URL patterns in a separate urls.py file
2. Implement new aggregated stats views
3. Add unit tests for new endpoints
4. Document new endpoints with OpenAPI/Swagger

## Testing Strategy

1. Unit tests for new v2 endpoints
2. Integration tests for data accuracy
3. Test cases for edge scenarios (empty games, no solos, etc.)

## Documentation

The new v2 endpoints will be documented with:
1. OpenAPI/Swagger specifications
2. Example requests and responses
3. Error scenarios
4. Authentication requirements

## Benefits

1. Maintains backward compatibility with v1 endpoints
2. Provides rich aggregated statistics
3. Enables better player performance analysis
4. Flexible filtering for player points
5. Consistent UUID usage in URLs