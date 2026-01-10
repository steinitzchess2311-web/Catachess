# Frontend Tests

Test suite for CataChess frontend components.

## 📁 Files

- **test_types.ts** - Type validation tests using sample messages
- **test_ws_mock.ts** - WebSocket client tests with mock server
- **test_runner.html** - Browser-based test runner
- **sample-messages.json** - Sample WebSocket messages from server
- **types.ts** - Full type definitions (reference)
- **connection-config.ts** - Server connection configuration

## 🧪 Running Tests

### Browser Tests

Open `test_runner.html` in a browser:

```bash
# From the tests directory
python3 -m http.server 8000

# Then open: http://localhost:8000/test_runner.html
```

The test runner will:
- Auto-run all tests on page load
- Display results in the browser
- Show colored output (green = success, red = error)
- Provide controls to re-run or clear output

### Node Tests (future)

```bash
# Install dependencies (when needed)
npm install

# Run tests
npm test
```

## 📊 Test Coverage

### Type Tests (`test_types.ts`)
- ✅ GameState type validation
- ✅ ServerMessage type validation
- ✅ Error message type validation

### WebSocket Tests (`test_ws_mock.ts`)
- ✅ Message parsing
- ✅ Game state updates
- ✅ Error handling
- ✅ Connection lifecycle

## 🔧 Adding New Tests

1. Create a new test file: `test_<feature>.ts`
2. Import types from `types.ts`
3. Use sample messages from `sample-messages.json`
4. Export a `run<Feature>Tests()` function
5. Add to `test_runner.html` imports

Example:

```typescript
import type { GameState } from './types';
import sampleMessages from './sample-messages.json';

export function runMyFeatureTests() {
    console.log('Running my feature tests...\n');

    // Your tests here

    console.log('✅ My feature tests passed!');
    return true;
}
```

## 📝 Sample Messages

The `sample-messages.json` file contains real message examples:

**Game States:**
- `game_state_initial` - Waiting for players
- `game_state_active` - Game in progress
- `game_state_mid_game` - Mid-game position
- `game_state_ended` - Game finished

**Errors:**
- `error_invalid_move` - Invalid move error
- `error_not_your_turn` - Wrong turn error
- `error_game_not_found` - Game not found error

**Other:**
- `ack` - Acknowledgment message
- Client messages (join, move, resign, etc.)

## 🎯 Test Philosophy

1. **Use Real Data** - All tests use actual server message formats
2. **Type Safety** - Test TypeScript types are correctly defined
3. **Mock When Needed** - Use mocks to avoid server dependency
4. **Fast Feedback** - Tests run in browser, instant results
5. **Easy to Run** - Single HTML file, no build step needed

## 📚 Resources

- Full protocol types: See `types.ts`
- Server config: See `connection-config.ts`
- Sample data: See `sample-messages.json`
- Server docs: See `../clauded_needed_resources/README.md`
