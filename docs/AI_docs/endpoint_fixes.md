# Endpoint Fixes Plan

## 1. Stats Endpoint Issue

### Current Problem
- The `/games/stats/` request is being caught by the games router which expects a UUID
- This results in a ValidationError as "stats" is not a valid UUID
- The actual stats endpoints are under different paths (`/stats/<uuid:player_id>/...`)

### Solution
1. Create a new dedicated endpoint for game stats
2. Reorder URL patterns in urls.py to ensure specific routes take precedence over router patterns
3. Move the router.urls include to the end of the urlpatterns

### Implementation Steps
1. Create new view function for game stats
2. Add new URL pattern before the router.urls include
3. Update URL patterns order in urls.py

```python
# New URL pattern to add before router.urls
path('games/stats/', views.get_game_stats, name='game_stats'),
```

## 2. Points Progression GIF Issue

### Current Problem
- 406 Not Acceptable error when requesting points progression GIF
- Indicates content negotiation issues with the Accept header

### Solution
1. Modify the view to explicitly handle content negotiation
2. Ensure proper content type headers are set
3. Add explicit Accept header handling

### Implementation Steps
1. Update get_points_progression_gif view to handle content negotiation:
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_points_progression_gif(request, game_id):
    # Add explicit content type negotiation
    if 'image/gif' not in request.accepted_media_types:
        return Response(
            {'error': 'Client must accept image/gif content type'},
            status=status.HTTP_406_NOT_ACCEPTABLE
        )
    
    # Rest of the existing view code...
```

2. Ensure client sends correct Accept header:
```
Accept: image/gif
```

## Testing Plan

1. Test stats endpoint:
```bash
curl -X GET http://localhost:8000/games/stats/
```

2. Test points progression GIF:
```bash
curl -X GET -H "Accept: image/gif" http://localhost:8000/games/{game_id}/points-progression-gif/
```

## Implementation Order

1. Implement stats endpoint fix first as it's causing immediate errors
2. Then implement points progression GIF fix
3. Test both changes thoroughly
4. Document API changes for frontend team

Would you like me to proceed with implementing these changes?