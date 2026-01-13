import { api } from '../../../assets/api';

export function initDiscussion(container: HTMLElement, options: { targetType: string, targetId: string }) {
    // 1. Load Template
    const template = document.getElementById('discussion-template') as HTMLTemplateElement;
    if (!template) return;
    const content = document.importNode(template.content, true);
    container.appendChild(content);

    const threadList = container.querySelector('#thread-list') as HTMLElement;
    const input = container.querySelector('#discussion-input') as HTMLTextAreaElement;
    const postBtn = container.querySelector('#post-comment-btn') as HTMLButtonElement;

    let { targetType, targetId } = options;

    const refreshThreads = async () => {
        try {
            // GET /api/v1/workspace/discussions?target_id=...&target_type=...
            const threads = await api.get(`/api/v1/workspace/discussions?target_id=${targetId}&target_type=${targetType}`);
            renderThreads(threads);
        } catch (error) {
            console.error('Failed to fetch discussions:', error);
        }
    };

    const renderThreads = (threads: any[]) => {
        threadList.innerHTML = '';
        const threadTpl = document.getElementById('thread-item-template') as HTMLTemplateElement;

        threads.forEach(thread => {
            const el = document.importNode(threadTpl.content, true);
            el.querySelector('.discussion-thread-author')!.textContent = thread.author_id; // Should map to username
            el.querySelector('.discussion-thread-date')!.textContent = new Date(thread.created_at).toLocaleString();
            el.querySelector('.discussion-thread-content')!.textContent = thread.content;
            
            threadList.appendChild(el);
        });
    };

    postBtn.addEventListener('click', async () => {
        const content = input.value.trim();
        if (!content) return;

        try {
            await api.post('/api/v1/workspace/discussions', {
                target_type: targetType,
                target_id: targetId,
                title: 'Comment', // Required by schema
                content: content,
                thread_type: 'comment'
            });
            input.value = '';
            refreshThreads();
        } catch (error) {
            console.error('Failed to post comment:', error);
        }
    });

    // Initial load
    refreshThreads();

    // Return an update function to change context
    return {
        updateContext: (newType: string, newId: string) => {
            targetType = newType;
            targetId = newId;
            refreshThreads();
        }
    };
}
