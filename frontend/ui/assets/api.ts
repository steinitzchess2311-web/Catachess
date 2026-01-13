export class ApiClient {
    private static instance: ApiClient;
    private baseURL: string;

    private constructor() {
        // Automatically determine base URL
        // In development (localhost), use localhost:8000
        // In production, use the production API URL
        this.baseURL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000'
            : 'https://api.catachess.com';
    }

    public static getInstance(): ApiClient {
        if (!ApiClient.instance) {
            ApiClient.instance = new ApiClient();
        }
        return ApiClient.instance;
    }

    public async request(endpoint: string, options: RequestInit = {}): Promise<any> {
        const token = localStorage.getItem('token');
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
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
                // Unauthorized - clear token and redirect
                localStorage.removeItem('token');
                // Only redirect if not already on login page to avoid loops
                if (!window.location.hash.includes('/login')) {
                    window.location.hash = '#/login';
                    console.warn('Unauthorized: Redirecting to login...');
                }
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
            body: JSON.stringify(body),
        });
    }

    public put(endpoint: string, body: any) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body),
        });
    }

    public delete(endpoint: string) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

export const api = ApiClient.getInstance();
