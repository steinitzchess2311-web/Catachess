import { api } from '../../../../assets/api';

export function initLogin(container: HTMLElement) {
    // 1. Load Template
    const template = document.getElementById('login-template') as HTMLTemplateElement;
    if (!template) {
        console.error('Login template not found');
        return;
    }
    const content = document.importNode(template.content, true);
    container.appendChild(content);

    // 2. Select Elements
    const form = container.querySelector('#login-form') as HTMLFormElement;
    const emailInput = container.querySelector('#email') as HTMLInputElement;
    const passwordInput = container.querySelector('#password') as HTMLInputElement;
    const errorDiv = container.querySelector('#login-error') as HTMLElement;
    const signupLink = container.querySelector('#link-signup') as HTMLAnchorElement;

    // 3. Event Listeners
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = emailInput.value;
        const password = passwordInput.value;

        // Clear previous errors
        errorDiv.textContent = '';

        try {
            // Call API
            // Note: Using OAuth2 form data structure as per backend spec
            const formData = new URLSearchParams();
            formData.append('username', email); // OAuth2 expects 'username' field
            formData.append('password', password);

            const response = await api.request('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString()
            });

            // Success
            if (response.access_token) {
                const token = response.access_token as string;
                localStorage.setItem('catachess_token', token);
                localStorage.setItem('catachess_token_type', response.token_type);
                const userId = decodeUserIdFromToken(token);
                if (userId) {
                    localStorage.setItem('catachess_user_id', userId);
                }
                // Redirect to workspace selection
                window.location.assign('/workspace-select');
            }
        } catch (error: any) {
            console.error('Login failed:', error);
            errorDiv.textContent = error.message || 'Invalid credentials';
        }
    });

    // Handle signup link navigation within SPA
    signupLink.addEventListener('click', (e) => {
        e.preventDefault();
        window.location.assign('/signup');
    });
}

function decodeUserIdFromToken(token: string) {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    try {
        let base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
        while (base64.length % 4) base64 += '=';
        const payload = JSON.parse(atob(base64));
        return typeof payload.sub === 'string' ? payload.sub : null;
    } catch {
        return null;
    }
}
