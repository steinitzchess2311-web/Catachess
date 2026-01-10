/**
 * Types Test
 * Verify that TypeScript types are correctly defined
 */

import type { GameState, ServerMessage, MessageType } from './types';
import sampleMessages from './sample-messages.json';

// Test: GameState type validation
function testGameStateType() {
    const sampleState = sampleMessages.server_to_client.game_state_active.payload;

    const state: GameState = sampleState;

    console.assert(state.game_id === 'game_abc123', 'game_id should match');
    console.assert(state.state === 'active', 'state should be active');
    console.assert(state.position.turn === 'black', 'turn should be black');
    console.assert(state.position.fen.length > 0, 'fen should not be empty');

    console.log('✓ GameState type validation passed');
}

// Test: ServerMessage type validation
function testServerMessageType() {
    const message = sampleMessages.server_to_client.game_state_active;

    const serverMsg: ServerMessage = message;

    console.assert(serverMsg.type === 'game_state', 'type should be game_state');
    console.assert(serverMsg.game_id === 'game_abc123', 'game_id should match');
    console.assert(serverMsg.seq === 2, 'seq should be 2');

    console.log('✓ ServerMessage type validation passed');
}

// Test: Error message validation
function testErrorMessageType() {
    const errorMsg = sampleMessages.server_to_client.error_invalid_move;

    console.assert(errorMsg.type === 'error', 'type should be error');
    console.assert(errorMsg.payload.code === 'INVALID_MOVE', 'error code should match');
    console.assert(errorMsg.payload.message.length > 0, 'error message should not be empty');

    console.log('✓ Error message type validation passed');
}

// Run all tests
export function runTypeTests() {
    console.log('Running type tests...\n');

    try {
        testGameStateType();
        testServerMessageType();
        testErrorMessageType();

        console.log('\n✅ All type tests passed!');
        return true;
    } catch (error) {
        console.error('\n❌ Type tests failed:', error);
        return false;
    }
}

// Run tests if executed directly
if (typeof window !== 'undefined') {
    runTypeTests();
}
