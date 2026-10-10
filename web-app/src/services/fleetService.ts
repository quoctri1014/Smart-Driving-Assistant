import { apiClient } from './apiClient';

export interface VehicleRecord {
  id: number;
  license_plate: string;
  vehicle_type: string;
  fleet_id?: number | null;
  branch_id?: number | null;
  status: string;
}

export interface DriverRecord {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  branch_id?: number | null;
  created_at?: string;
}

class FleetService {
  async getVehicles(): Promise<VehicleRecord[]> {
    return apiClient.get<VehicleRecord[]>('/api/v1/fleet/vehicles');
  }

  async getVehicleDetail(id: number): Promise<VehicleRecord> {
    return apiClient.get<VehicleRecord>(`/api/v1/fleet/vehicles/${id}`);
  }

  async getDrivers(): Promise<DriverRecord[]> {
    return apiClient.get<DriverRecord[]>('/api/v1/fleet/drivers');
  }
}

export const fleetService = new FleetService();
