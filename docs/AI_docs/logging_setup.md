# Logging Setup for Doko API

## Overview
This document describes the logging configuration for the Doko API project. The logging system is designed to provide detailed debugging information while maintaining clean production logs.

## Configuration

### Log Levels
- DEBUG: Detailed information for debugging
- INFO: General operational events
- WARNING: Unexpected but handled events
- ERROR: Serious issues that need attention
- CRITICAL: Critical issues that may cause system failure

### Log Format
```python
{
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/doko_api.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'doko_api': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Implementation Steps

1. Create a new Python module `doko_api/logging_config.py` with the logging configuration
2. Update Django settings to use this configuration
3. Create a logs directory in the project root
4. Add logging statements to the views_v2 file to debug the stats endpoints

## Usage Example

```python
import logging

# Get logger for the module
logger = logging.getLogger('doko_api.views_v2')

def get_game_points(request, player_uuid):
    logger.debug(f"Getting game points for player {player_uuid}")
    try:
        player = Player.objects.get(player_id=player_uuid)
    except Player.DoesNotExist:
        logger.warning(f"Player {player_uuid} not found")
        return Response({'error': 'Player not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Log query parameters
    logger.debug(f"Query params: {request.query_params}")
    
    # Log database queries
    points = PlayerPoints.objects.filter(
        player=player,
        games__isnull=False,
        games__flag_removed=False
    )
    logger.debug(f"Found {points.count()} game points")
```

## Benefits

1. Consistent logging format across the application
2. Rotating file logs to manage disk space
3. Different log levels for development and production
4. Easy debugging with detailed context
5. Performance monitoring capabilities

Would you like me to proceed with implementing this logging setup?