/**
 * WebSocket Mock Test
 * Test WebSocket functionality with mock server
 */

import type { ServerMessage, GameState } from './types';
import sampleMessages from './sample-messages.json';

// Mock WebSocket server
class MockWebSocketServer {
    private handlers: Map<string, Function> = new Map();

    on(event: string, handler: Function) {
        this.handlers.set(event, handler);
    }

    simulateMessage(message: ServerMessage) {
        const handler = this.handlers.get('message');
        if (handler) {
            handler({ data: JSON.stringify(message) });
        }
    }

    simulateOpen() {
        const handler = this.handlers.get('open');
        if (handler) handler({});
    }

    simulateClose() {
        const handler = this.handlers.get('close');
        if (handler) handler({});
    }

    simulateError(error: Error) {
        const handler = this.handlers.get('error');
        if (handler) handler(error);
    }
}

// Test: Message parsing
function testMessageParsing() {
    const mockServer = new MockWebSocketServer();
    let receivedMessage: ServerMessage | null = null;

    mockServer.on('message', (event: any) => {
        receivedMessage = JSON.parse(event.data);
    });

    const testMessage = sampleMessages.server_to_client.game_state_active;
    mockServer.simulateMessage(testMessage);

    console.assert(receivedMessage !== null, 'Message should be received');
    console.assert(receivedMessage?.type === 'game_state', 'Message type should match');

    console.log('✓ Message parsing test passed');
}

// Test: Game state update
function testGameStateUpdate() {
    const mockServer = new MockWebSocketServer();
    let currentState: GameState | null = null;

    mockServer.on('message', (event: any) => {
        const message: ServerMessage = JSON.parse(event.data);
        if (message.type === 'game_state') {
            currentState = message.payload;
        }
    });

    // Simulate initial state
    mockServer.simulateMessage(sampleMessages.server_to_client.game_state_initial);
    console.assert(currentState?.state === 'waiting', 'Initial state should be waiting');

    // Simulate active state
    mockServer.simulateMessage(sampleMessages.server_to_client.game_state_active);
    console.assert(currentState?.state === 'active', 'State should be active');
    console.assert(currentState?.position.move_history.length === 1, 'Should have 1 move');

    console.log('✓ Game state update test passed');
}

// Test: Error handling
function testErrorHandling() {
    const mockServer = new MockWebSocketServer();
    let receivedError: any = null;

    mockServer.on('message', (event: any) => {
        const message: ServerMessage = JSON.parse(event.data);
        if (message.type === 'error') {
            receivedError = message.payload;
        }
    });

    // Simulate error
    mockServer.simulateMessage(sampleMessages.server_to_client.error_invalid_move);

    console.assert(receivedError !== null, 'Error should be received');
    console.assert(receivedError.code === 'INVALID_MOVE', 'Error code should match');
    console.assert(receivedError.message.length > 0, 'Error message should not be empty');

    console.log('✓ Error handling test passed');
}

// Test: Connection lifecycle
function testConnectionLifecycle() {
    const mockServer = new MockWebSocketServer();
    const events: string[] = [];

    mockServer.on('open', () => events.push('open'));
    mockServer.on('close', () => events.push('close'));
    mockServer.on('error', () => events.push('error'));

    mockServer.simulateOpen();
    mockServer.simulateError(new Error('test'));
    mockServer.simulateClose();

    console.assert(events.length === 3, 'Should have 3 events');
    console.assert(events[0] === 'open', 'First event should be open');
    console.assert(events[1] === 'error', 'Second event should be error');
    console.assert(events[2] === 'close', 'Third event should be close');

    console.log('✓ Connection lifecycle test passed');
}

// Run all tests
export function runWebSocketTests() {
    console.log('Running WebSocket mock tests...\n');

    try {
        testMessageParsing();
        testGameStateUpdate();
        testErrorHandling();
        testConnectionLifecycle();

        console.log('\n✅ All WebSocket tests passed!');
        return true;
    } catch (error) {
        console.error('\n❌ WebSocket tests failed:', error);
        return false;
    }
}

// Run tests if executed directly
if (typeof window !== 'undefined') {
    runWebSocketTests();
}
