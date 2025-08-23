# Points Progression API Specification

## Endpoints

### 1. Get Points Progression GIF
Generates an animated GIF showing the progression of points throughout the game.

```
GET /games/{game_id}/points-progression-gif/
```

#### Parameters
- `game_id` (UUID, required): The unique identifier of the game
- `duration` (integer, optional): Duration of each frame in milliseconds. Default: 500

#### Response
- Content-Type: `image/gif`
- Content-Disposition: `inline; filename="game_{game_id}_progression.gif"`

#### Example Usage
```typescript
// Using fetch
const getPointsProgressionGif = async (gameId: string, duration: number = 500) => {
  const response = await fetch(
    `${API_BASE_URL}/games/${gameId}/points-progression-gif/?duration=${duration}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch points progression GIF');
  }
  
  // For displaying in an img tag
  const blob = await response.blob();
  const imageUrl = URL.createObjectURL(blob);
  return imageUrl;
};

// Usage in React component
const PointsProgressionGif: React.FC<{ gameId: string }> = ({ gameId }) => {
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  useEffect(() => {
    const loadGif = async () => {
      try {
        const url = await getPointsProgressionGif(gameId);
        setImageUrl(url);
      } catch (error) {
        console.error('Error loading points progression:', error);
      }
    };
    loadGif();
  }, [gameId]);

  return imageUrl ? (
    <img 
      src={imageUrl} 
      alt="Points Progression" 
      style={{ maxWidth: '100%', height: 'auto' }} 
    />
  ) : (
    <div>Loading...</div>
  );
};
```

### 2. Get Points Progression Static Image
Generates a static PNG image showing the complete points progression.

```
GET /games/{game_id}/points-progression-image/
```

#### Parameters
- `game_id` (UUID, required): The unique identifier of the game

#### Response
- Content-Type: `image/png`
- Content-Disposition: `inline; filename="game_{game_id}_progression.png"`

#### Example Usage
```typescript
// Using fetch
const getPointsProgressionImage = async (gameId: string) => {
  const response = await fetch(
    `${API_BASE_URL}/games/${gameId}/points-progression-image/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch points progression image');
  }
  
  // For displaying in an img tag
  const blob = await response.blob();
  const imageUrl = URL.createObjectURL(blob);
  return imageUrl;
};

// Usage in React component
const PointsProgressionImage: React.FC<{ gameId: string }> = ({ gameId }) => {
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  useEffect(() => {
    const loadImage = async () => {
      try {
        const url = await getPointsProgressionImage(gameId);
        setImageUrl(url);
      } catch (error) {
        console.error('Error loading points progression:', error);
      }
    };
    loadImage();
  }, [gameId]);

  return imageUrl ? (
    <img 
      src={imageUrl} 
      alt="Points Progression" 
      style={{ maxWidth: '100%', height: 'auto' }} 
    />
  ) : (
    <div>Loading...</div>
  );
};
```

## Error Responses

Both endpoints return the following error response when the game is not found:

```json
{
  "error": "Game not found."
}
```

Status Code: 404

## Authentication

Both endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Visualization Details

The generated visualizations include:
- Line graph showing points progression over time
- Different colored lines for each player
- Points marked with dots at each round
- Legend showing player names
- Grid lines for better readability
- Clear labels for axes and title

## Usage Notes

1. The GIF endpoint allows customization of animation speed through the `duration` parameter
2. Both endpoints return the image data directly, suitable for:
   - Displaying in `<img>` tags
   - Downloading as files
   - Embedding in other UI elements
3. The static image is more suitable for:
   - Faster loading times
   - Lower bandwidth usage
   - Printing or saving
4. The animated GIF is better for:
   - Showing the progression over time
   - Presentations
   - Interactive displays

## Integration Tips

1. Consider implementing loading states while fetching the images
2. Handle errors appropriately and show user-friendly error messages
3. Implement caching to avoid unnecessary requests
4. Consider implementing a refresh mechanism for real-time updates
5. Add error boundaries to handle rendering failures gracefully

Example error handling:

```typescript
const PointsProgression: React.FC<{ gameId: string; type: 'gif' | 'static' }> = ({ gameId, type }) => {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadImage = async () => {
      try {
        setLoading(true);
        setError(null);
        const url = type === 'gif' 
          ? await getPointsProgressionGif(gameId)
          : await getPointsProgressionImage(gameId);
        setImageUrl(url);
      } catch (error) {
        setError('Failed to load points progression visualization');
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };
    loadImage();

    // Cleanup
    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [gameId, type]);

  if (loading) {
    return <div>Loading points progression...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return imageUrl ? (
    <img 
      src={imageUrl} 
      alt="Points Progression" 
      style={{ maxWidth: '100%', height: 'auto' }} 
    />
  ) : null;
};