# Points Endpoint Improvement Plan

## Current Issue
The current filtered points endpoint doesn't properly distinguish between two types of points in Doppelkopf:
1. Game Points: Aggregated points for an entire evening/game session
2. Round Points: Individual points from each round that make up a game

## Proposed Solution

### Option 1: Split into Two Endpoints

Create two distinct endpoints:

1. GET /v2/players/{uuid}/game-points/
   - Returns only game-level aggregated points
   - Parameters:
     * start_date: Filter by date
     * end_date: Filter by date
     * is_game_closed: Filter by game status
     * sort_by: points, date
     * sort_order: asc, desc
   - Response includes:
     * game_id
     * game_name
     * total_points
     * created_at
     * closed_at
     * total_rounds
     * solo_count
     * final_position

2. GET /v2/players/{uuid}/round-points/
   - Returns individual round points
   - Parameters:
     * start_date: Filter by date
     * end_date: Filter by date
     * game_id: Filter by specific game
     * game_type: normal, solo, pflichtsolo
     * sort_by: points, date
     * sort_order: asc, desc
   - Response includes:
     * round_id
     * game_id
     * points
     * was_solo
     * was_pflichtsolo
     * bock_multiplier
     * created_at

### Option 2: Single Endpoint with Type Parameter

Modify current endpoint to support type selection:

GET /v2/players/{uuid}/points/
- New parameter:
  * type: game | round | all (default: all)
- Other parameters:
  * start_date
  * end_date
  * game_id
  * game_type (only for round points)
  * is_game_closed
  * sort_by
  * sort_order
- Response format when type=all:
```json
{
  "total_count": 123,
  "points": [
    {
      "type": "game",
      "game_id": "uuid",
      "game_name": "Evening Game",
      "points": 240,
      "created_at": "2024-02-19T20:00:00Z",
      "closed_at": "2024-02-19T23:00:00Z",
      "total_rounds": 12,
      "solo_count": 1
    },
    {
      "type": "round",
      "round_id": "uuid",
      "game_id": "uuid",
      "points": 20,
      "was_solo": false,
      "was_pflichtsolo": false,
      "bock_multiplier": 1,
      "created_at": "2024-02-19T20:15:00Z"
    }
  ],
  "aggregates": {
    "total_points": 1234,
    "average_points": 45.6,
    "min_points": -30,
    "max_points": 120
  }
}
```

## Recommendation

Recommend implementing Option 1 (Split into Two Endpoints) because:
1. Clearer separation of concerns
2. More intuitive API design
3. Easier to maintain and extend
4. Better alignment with REST principles
5. Simpler parameter handling
6. More focused responses

## Implementation Steps

1. Create new endpoints in urls_v2.py
2. Split current get_filtered_player_points into two functions
3. Update Swagger documentation
4. Add new test cases
5. Update existing tests to use correct endpoint
6. Add deprecation warning to old endpoint if needed

## Migration Strategy

1. Implement new endpoints
2. Keep existing endpoint temporarily
3. Add deprecation warning to existing endpoint
4. Give users time to migrate (e.g., 3 months)
5. Remove old endpoint in future version

Would you like me to proceed with implementing this improvement?