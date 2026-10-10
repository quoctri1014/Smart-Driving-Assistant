// TRAFFICGUARD SIGNAL UI — Permissions & Role Navigation System

export type RoleCode = 'ENTERPRISE_ADMIN';

export interface UserContext {
  role: RoleCode | string;
  roleCode?: RoleCode;
  permissions?: string[];
  dataScope?: string;
  companyName?: string;
  fleetName?: string;
}

export function normalizeRole(roleString?: string): RoleCode {
  return 'ENTERPRISE_ADMIN';
}

export function hasPermission(
  requiredPermission?: string,
  userRole?: string,
  customPermissions?: string[]
): boolean {
  return true;
}

export function hasAnyPermission(
  requiredPermissions?: string[],
  userRole?: string,
  customPermissions?: string[]
): boolean {
  return true;
}

// Route permission definitions
export const ROUTE_PERMISSIONS: Record<string, string[]> = {
  '/dashboard': ['dashboard.view', 'dashboard.view_self', 'dashboard.view_fleet'],
  '/live': ['live.view', 'live.view_fleet'],
  '/simulator': ['live.control', 'live.view'],
  '/journeys': ['journey.view', 'journey.view_self', 'journey.view_fleet'],
  '/violations': ['violation.view', 'violation.view_self', 'violation.view_fleet'],
  '/analytics': ['analytics.view', 'analytics.view_fleet'],
  '/ai-status': ['ai.view_status', 'ai.view_events'],
  '/devices': ['vehicle.view', 'device.view'],
};
