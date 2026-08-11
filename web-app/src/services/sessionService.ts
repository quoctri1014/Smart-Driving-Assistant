import { apiClient } from './apiClient';

export interface JourneySession {
  id: number;
  driver_id: number;
  start_time: string;
  end_time?: string;
  total_minutes?: number;
}

export interface SessionResetResponse {
  message: string;
  session_id: number;
}

class SessionService {
  async getSessions(skip: number = 0, limit: number = 50): Promise<JourneySession[]> {
    return apiClient.get<JourneySession[]>(`/api/sessions/?skip=${skip}&limit=${limit}`);
  }

  async resetRest(): Promise<SessionResetResponse> {
    return apiClient.post<SessionResetResponse>('/api/sessions/reset-rest');
  }
}

export const sessionService = new SessionService();
