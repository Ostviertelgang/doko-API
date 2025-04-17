# Stats Removal and API Simplification Plan

## Files to Modify

### 1. urls_v2.py
Remove all stats-related endpoints:
- /players/{uuid}/summary-stats/
- /players/{uuid}/game-type-stats/
- /players/{uuid}/game-points/
- /players/{uuid}/round-points/

### 2. views_v2.py
Remove functions:
- get_player_summary_stats
- get_game_type_stats
- get_game_points
- get_round_points

### 3. models.py
Keep the essential fields, focusing on:
- Player model with basic fields
- Game model relationships
- Round model core functionality

## Implementation Steps

1. Remove Stats Endpoints
- Delete all stats-related URL patterns
- Remove corresponding view functions
- Remove Swagger documentation for stats endpoints

2. Clean Up Dependencies
- Remove unused imports
- Clean up any stats-related constants or schemas

3. Keep Essential Player Features
- Basic player profile (name, ID)
- Game participation tracking
- Simple round points recording

4. Add Basic Group Permissions
- Admin group: Full access
- Staff: Game management
- Player: Profile management

## Migration Notes
- No database migrations needed as we're only removing endpoints
- Existing data structure remains unchanged
- Only removing API access to stats functionality

This plan aligns with the user's request to remove stats endpoints while maintaining basic player management functionality.