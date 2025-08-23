# Stats Endpoints Test Plan

## Understanding Doppelkopf Game Structure

### Game Components
1. Players
   - Always 4 players per game
   - Each player must play one Pflichtsolo (mandatory solo)

2. Round Types
   - Normal rounds (2 winners, 2 losers)
   - Solo rounds (1 winner, 3 losers)
   - Pflichtsolo rounds (mandatory solo)
   - Bock rounds (point multipliers)

3. Points System
   - Normal rounds: Winners get +points, losers get -points
   - Solo rounds: Winner gets 3x points, losers each get -points
   - Points are affected by bock multipliers
   - Points accumulate over multiple rounds

## Test Cases Required

### 1. Player Summary Stats
- Test normal game progression
  * Multiple normal rounds
  * Points accumulation
  * Win rate calculation
- Test solo performance
  * Solo rounds with wins/losses
  * Pflichtsolo tracking
  * Solo-specific win rates
- Test with bock multipliers
  * Single bock effects
  * Double bock effects
  * Cascading bock rounds

### 2. Game Type Stats
- Normal games stats
  * Count of normal rounds
  * Win rate in normal rounds
  * Average points in normal rounds
- Solo games stats
  * Separate tracking for regular solos and pflichtsolos
  * Win rates for each solo type
  * Points distribution in solo rounds
- Bock rounds stats
  * Proper multiplier tracking
  * Points calculation with multipliers
  * Bock round progression

### 3. Points Progression
- Basic points tracking
  * Round-by-round accumulation
  * Game total calculations
  * Position tracking
- Game type variations
  * Points from normal rounds
  * Points from solo rounds
  * Points from bock rounds
- Complex scenarios
  * Multiple bock multipliers
  * Solo during bock rounds
  * Pflichtsolo completion tracking

### 4. Filtered Points
- Game type filtering
  * Filter by normal games
  * Filter by solo games
  * Filter by pflichtsolo games
- Date range filtering
  * Recent games
  * Historical games
  * Custom date ranges
- Sorting options
  * Sort by points
  * Sort by date
  * Sort by game type

## Test Implementation Plan

1. Setup Improvements
   - Create proper 4-player game setup
   - Add helper methods for different round types
   - Include bock round tracking
   - Setup test data with various game scenarios

2. Test Structure
   - Organize tests by endpoint
   - Create helper methods for common operations
   - Use clear test names describing scenarios
   - Include proper assertions for all cases

3. Test Data Requirements
   - Create games with all round types
   - Include bock and double bock scenarios
   - Track pflichtsolo completion
   - Generate realistic point distributions

4. Edge Cases to Cover
   - Solo during bock rounds
   - Multiple consecutive bock rounds
   - All players completing pflichtsolo
   - Games with extreme point differences