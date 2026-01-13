import { api } from '../../../assets/api';

export function initSignup(container: HTMLElement) {
    // 1. Load Template
    const template = document.getElementById('signup-template') as HTMLTemplateElement;
    if (!template) {
        console.error('Signup template not found');
        return;
    }
    const content = document.importNode(template.content, true);
    container.appendChild(content);

    // 2. Select Elements
    const step1 = container.querySelector('#signup-step-1') as HTMLElement;
    const step2 = container.querySelector('#signup-step-2') as HTMLElement;
    
    const signupForm = container.querySelector('#signup-form') as HTMLFormElement;
    const emailInput = container.querySelector('#signup-email') as HTMLInputElement;
    const usernameInput = container.querySelector('#signup-username') as HTMLInputElement;
    const passwordInput = container.querySelector('#signup-password') as HTMLInputElement;
    const signupError = container.querySelector('#signup-error') as HTMLElement;
    const loginLink = container.querySelector('#link-login') as HTMLAnchorElement;

    const verificationForm = container.querySelector('#verification-form') as HTMLFormElement;
    const codeInput = container.querySelector('#verification-code') as HTMLInputElement;
    const verificationError = container.querySelector('#verification-error') as HTMLElement;
    const verificationEmailSpan = container.querySelector('#verification-email') as HTMLElement;
    const resendBtn = container.querySelector('#resend-btn') as HTMLButtonElement;
    const resendTimer = container.querySelector('#resend-timer') as HTMLElement;

    // State
    let userEmail = '';
    let resendCountdown = 0;
    let timerInterval: any = null;

    // 3. Helper Functions
    const startTimer = () => {
        resendCountdown = 60;
        resendBtn.disabled = true;
        resendTimer.classList.remove('hidden');
        
        timerInterval = setInterval(() => {
            resendCountdown--;
            resendTimer.textContent = `in ${resendCountdown}s`;
            
            if (resendCountdown <= 0) {
                clearInterval(timerInterval);
                resendBtn.disabled = false;
                resendTimer.classList.add('hidden');
            }
        }, 1000);
    };

    const showStep2 = () => {
        step1.classList.add('hidden');
        step2.classList.remove('hidden');
        verificationEmailSpan.textContent = userEmail;
        startTimer();
    };

    // 4. Event Listeners

    // Step 1: Register
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        userEmail = emailInput.value;
        const username = usernameInput.value;
        const password = passwordInput.value;

        signupError.textContent = '';

        try {
            await api.post('/auth/register', {
                identifier: userEmail,
                identifier_type: 'email',
                password: password,
                username: username || undefined
            });
            
            showStep2();
        } catch (error: any) {
            console.error('Registration failed:', error);
            signupError.textContent = error.message || 'Registration failed';
        }
    });

    // Step 2: Verify
    verificationForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = codeInput.value;

        verificationError.textContent = '';

        try {
            await api.post('/auth/verify-signup', {
                identifier: userEmail,
                code: code
            });

            // Success - Redirect to Login
            alert('Account verified successfully! Please log in.');
            window.location.hash = '/login';
        } catch (error: any) {
            console.error('Verification failed:', error);
            verificationError.textContent = error.message || 'Invalid code';
        }
    });

    // Resend Code
    resendBtn.addEventListener('click', async () => {
        if (resendCountdown > 0) return;

        try {
            await api.post('/auth/resend-verification', {
                identifier: userEmail
            });
            startTimer();
        } catch (error: any) {
            console.error('Resend failed:', error);
            verificationError.textContent = error.message || 'Failed to resend code';
        }
    });

    // Navigate to login
    loginLink.addEventListener('click', (e) => {
        e.preventDefault();
        window.location.hash = '/login';
    });
}
