export class ApiClient {
    private static instance: ApiClient;
    private baseURL: string;

    private static resolveApiBase(): string {
        const envBase = import.meta.env.VITE_API_BASE as string | undefined;
        if (envBase) return envBase;
        const host = window.location.hostname;
        if (host === 'localhost' || host === '127.0.0.1') {
            return 'http://localhost:8000';
        }
        return 'https://api.catachess.com';
    }

    private constructor() {
        // Automatically determine base URL, with env override
        this.baseURL = ApiClient.resolveApiBase();
    }

    public static getInstance(): ApiClient {
        if (!ApiClient.instance) {
            ApiClient.instance = new ApiClient();
        }
        return ApiClient.instance;
    }

    public async request(endpoint: string, options: RequestInit = {}): Promise<any> {
        const token =
            localStorage.getItem('catachess_token') ||
            sessionStorage.getItem('catachess_token');

        // Don't set Content-Type for FormData (browser will set it with boundary)
        const isFormData = options.body instanceof FormData;
        const headers: Record<string, string> = {
            ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
            ...(options.headers as Record<string, string>),
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                ...options,
                headers,
            });

            if (response.status === 401) {
                // Clear stored credentials so the next Protected route check redirects to login
                localStorage.removeItem('catachess_token');
                localStorage.removeItem('catachess_user_id');
                sessionStorage.removeItem('catachess_token');
                sessionStorage.removeItem('catachess_user_id');
                throw new Error('Unauthorized');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Request failed with status ${response.status}`);
            }

            // Handle 204 No Content
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Failed:', error);
            throw error;
        }
    }

    public get(endpoint: string) {
        return this.request(endpoint, { method: 'GET' });
    }

    public post(endpoint: string, body: any) {
        return this.request(endpoint, {
            method: 'POST',
            body: body instanceof FormData ? body : JSON.stringify(body),
        });
    }

    public put(endpoint: string, body: any) {
        return this.request(endpoint, {
            method: 'PUT',
            body: body instanceof FormData ? body : JSON.stringify(body),
        });
    }

    public delete(endpoint: string) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

export const api = ApiClient.getInstance();
