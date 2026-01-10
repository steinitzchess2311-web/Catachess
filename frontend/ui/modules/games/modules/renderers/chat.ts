/**
 * Chat Renderer - Chat messages display
 */

export class ChatRenderer {
    private chatMessages: HTMLElement;

    constructor() {
        this.chatMessages = document.getElementById('chat-messages')!;
    }

    addMessage(message: string, sender?: string): void {
        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message';

        if (sender) {
            messageEl.innerHTML = `<strong>${sender}:</strong> ${message}`;
        } else {
            messageEl.textContent = message;
        }

        this.chatMessages.appendChild(messageEl);

        // Auto-scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    clear(): void {
        this.chatMessages.innerHTML = '';
    }
}
