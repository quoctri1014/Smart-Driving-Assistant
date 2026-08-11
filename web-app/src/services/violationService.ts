import { apiClient } from './apiClient';

export interface Violation {
  id: number;
  driver_id: number;
  violation_type: string; // e.g., "helmet", "speed", "collision"
  confidence: number;
  timestamp: string;
  image_path?: string;
  plate_text?: string;
  metadata_json?: any;
}

class ViolationService {
  async getViolations(skip: number = 0, limit: number = 50, type?: string): Promise<Violation[]> {
    const typeParam = type ? `&violation_type=${encodeURIComponent(type)}` : '';
    return apiClient.get<Violation[]>(`/api/violations/?skip=${skip}&limit=${limit}${typeParam}`);
  }
}

export const violationService = new ViolationService();
