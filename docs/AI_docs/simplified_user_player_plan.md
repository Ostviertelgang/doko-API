# Simplified User-Player Management Plan

## Current State
- Basic Django User model
- Simple Player model with name and UUID
- No proper User-Player relationship (currently commented out)
- Basic token authentication
- No role-based access control

## Simplified Improvements

### 1. User-Player Relationship
- Implement clean one-to-one relationship between User and Player
- Keep the Player model simple with just essential fields:
  * name (existing)
  * player_id (existing UUID)
  * user (new OneToOne field)
  * flag_removed (existing)

### 2. Authentication & Authorization
- Keep the existing token authentication
- Add basic password reset functionality
- Add simple email verification for new users
- Implement Django's built-in group-based permissions:
  * Create default groups (Admin, Staff, Player)
  * Define permissions per group:
    - Admin: Full access to all features
    - Player: Basic game participation, and writing down games, profile management
  * Easy to extend with new groups/permissions in future

### 3. Profile (Minimal)
Add only essential profile fields to Player model:
- join_date (DateTimeField, auto_now_add)
- last_active (DateTimeField, auto_now)

### 4. API Endpoints
Simple endpoints for:
- Player profile view/edit (name only)
- Basic account management (password reset, email verification)
- Group-specific endpoints:
  * Admin: User/player management, group management
  * Staff: Game management
  * Player: Profile, game participation

## Implementation Plan

### Phase 1: Core Model Update
1. Update Player model with User relationship
2. Create migration for existing data
3. Update serializers

### Phase 2: Auth & Permissions Setup
1. Create default groups (Admin, Staff, Player)
2. Define base permissions for each group
3. Add permission decorators to views
4. Add password reset functionality
5. Add simple email verification
6. Update authentication views

### Phase 3: Simple Profile
1. Add minimal profile fields to Player model
2. Create profile endpoints
3. Update API documentation

## Technical Details

### Model Changes
```python
class Player(models.Model):
    name = models.CharField(max_length=200)
    player_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    join_date = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    flag_removed = models.BooleanField(default=False)
```

### Permission Groups Setup
```python
# Initial groups and permissions
GROUPS = {
    'Admin': {
        'permissions': [
            'add_player', 'change_player', 'delete_player',
            'add_game', 'change_game', 'delete_game',
            'manage_groups'
        ]
    },
    'Staff': {
        'permissions': [
            'add_game', 'change_game',
            'view_player', 'change_player'
        ]
    },
    'Player': {
        'permissions': [
            'view_game',
            'view_player',
            'change_own_profile'
        ]
    }
}
```

### New API Endpoints
- GET/PATCH /api/v2/profile/ - View/update own profile
- POST /api/v2/auth/password-reset/ - Request password reset
- POST /api/v2/auth/verify-email/ - Verify email
- Admin endpoints:
  * GET/POST /api/v2/admin/users/ - User management
  * GET/POST /api/v2/admin/groups/ - Group management
- Staff endpoints:
  * GET/POST /api/v2/staff/games/ - Game management

### Security
- Django's built-in permission system
- Group-based access control
- Basic input validation
- Standard Django authentication checks
- Simple error handling

### Decorators
```python
from django.contrib.auth.decorators import permission_required
from functools import wraps

def group_required(group_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden()
        return _wrapped_view
    return decorator
```

## Testing
1. Unit tests for User-Player relationship
2. Permission group tests
3. Basic API endpoint tests
4. Authentication flow tests
5. Group-based access control tests

## Migration Strategy
1. Add new fields without breaking existing functionality
2. Link existing players to users where possible
3. Create initial groups and assign permissions
4. Keep backward compatibility

## Future Extensibility
The group-based permission system makes it easy to:
1. Add new roles (e.g., Moderator, Tournament Admin)
2. Define granular permissions per group
3. Add new protected endpoints
4. Implement feature flags per group

This simplified plan focuses on essential functionality while implementing proper role-based access control using Django's built-in systems. It avoids complex features like statistics and friend systems but provides a solid foundation for future extensions through the group-based permission system.