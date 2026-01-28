/**
 * CataMaze API Client
 */

const BASE_URL = process.env.REACT_APP_API_URL || 'https://catamazeapi.catachess.com';

export interface Position {
  x: number;
  y: number;
}

export interface Observation {
  entity_id: string;
  hp: number;
  ammo: number;
  time: number;
  position: Position;
  vision: string[][];
  last_sound: string | null;
  alive: boolean;
  won: boolean;
  game_over: boolean;
}

export interface NewGameResponse {
  game_id: string;
  observation: Observation;
  queue_size: number;
}

export interface ActionResponse {
  success: boolean;
  queue_size: number;
  message: string;
}

export interface TickResponse {
  tick: number;
  observation: Observation;
  events: string[];
  queue_size: number;
}

export interface ObserveResponse {
  observation: Observation;
}

export interface ResumeResponse {
  game_id: string;
  observation: Observation;
  queue_size: number;
}

export class CataMazeAPIClient {
  private baseURL: string;

  constructor(baseURL: string = BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    method: 'GET' | 'POST' = 'GET',
    body?: any
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async createGame(): Promise<NewGameResponse> {
    return this.request<NewGameResponse>('/game/new', 'POST');
  }

  async submitAction(game_id: string, action: string): Promise<ActionResponse> {
    return this.request<ActionResponse>('/game/action', 'POST', {
      game_id,
      action,
    });
  }

  async executeTick(game_id: string): Promise<TickResponse> {
    return this.request<TickResponse>('/game/tick', 'POST', { game_id });
  }

  async clearQueue(game_id: string): Promise<{ success: boolean; message: string }> {
    return this.request('/game/clear_queue', 'POST', { game_id });
  }

  async resumeGame(game_id: string): Promise<ResumeResponse> {
    return this.request<ResumeResponse>('/game/resume', 'POST', { game_id });
  }

  async observeGame(game_id: string): Promise<ObserveResponse> {
    return this.request<ObserveResponse>(`/game/observe?game_id=${game_id}`);
  }
}

export const apiClient = new CataMazeAPIClient();
