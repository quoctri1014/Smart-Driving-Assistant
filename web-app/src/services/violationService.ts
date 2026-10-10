import { apiClient } from './apiClient';

export interface ViolationReviewItem {
  id: number;
  reviewer_id: number;
  reviewer_name: string;
  action: string;
  old_review_status: string;
  new_review_status: string;
  old_resolution_status: string;
  new_resolution_status: string;
  note: string;
  created_at: string;
}

export interface Violation {
  id: number;
  organization_id: number;
  fleet_id?: number;
  driver_id: number;
  vehicle_id?: number;
  session_id?: number;
  violation_type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  review_status: 'PENDING_REVIEW' | 'NEEDS_EVIDENCE' | 'CONFIRMED' | 'FALSE_POSITIVE';
  resolution_status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
  status: string;
  confidence: number | null;
  source_module?: string;
  model_version?: string;
  speed_kph?: number;
  speed_limit_kph?: number;
  latitude?: number;
  longitude?: number;
  location_name?: string;
  detected_at: string;
  timestamp?: string;
  has_evidence: boolean;
  image_path?: string;
  reviewed_by?: number;
  review_notes?: string;
  reviewed_at?: string;
  resolved_at?: string;
  version: number;
  driver_name?: string;
  driver_phone?: string;
  vehicle_plate?: string;
  plate_text?: string;
  fleet_name?: string;
  reviews?: ViolationReviewItem[];
}

export interface ViolationQueryParams {
  skip?: number;
  limit?: number;
  violation_type?: string;
  review_status?: string;
  resolution_status?: string;
  severity?: string;
  min_confidence?: number;
  search?: string;
}

class ViolationService {
  async getViolations(params?: ViolationQueryParams): Promise<Violation[]> {
    const query = new URLSearchParams();
    if (params?.skip !== undefined) query.set('skip', String(params.skip));
    if (params?.limit !== undefined) query.set('limit', String(params.limit));
    if (params?.violation_type) query.set('violation_type', params.violation_type);
    if (params?.review_status) query.set('review_status', params.review_status);
    if (params?.resolution_status) query.set('resolution_status', params.resolution_status);
    if (params?.severity) query.set('severity', params.severity);
    if (params?.min_confidence !== undefined) query.set('min_confidence', String(params.min_confidence));
    if (params?.search) query.set('search', params.search);

    const queryString = query.toString();
    const url = `/api/v1/violations/${queryString ? `?${queryString}` : ''}`;
    return apiClient.get<Violation[]>(url);
  }

  async getViolationDetail(id: number): Promise<Violation> {
    return apiClient.get<Violation>(`/api/v1/violations/${id}`);
  }

  async reviewViolation(id: number, action: string, note: string, expectedVersion?: number): Promise<any> {
    return apiClient.post(`/api/v1/violations/${id}/review`, {
      action,
      note,
      expected_version: expectedVersion
    });
  }

  async recordViolation(payload: {
    violation_type: string;
    severity?: 'INFO' | 'WARNING' | 'CRITICAL';
    confidence?: number;
    source_module?: string;
    speed_kph?: number;
    speed_limit_kph?: number;
    latitude?: number;
    longitude?: number;
    location_name?: string;
    image_base64?: string;
    notes?: string;
    vehicle_id?: number;
    session_id?: number;
  }): Promise<any> {
    return apiClient.post('/api/v1/violations', payload);
  }
}

export const violationService = new ViolationService();
