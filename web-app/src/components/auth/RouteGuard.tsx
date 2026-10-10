'use client';

import React from 'react';

export interface RouteGuardProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requiredPermissions?: string[];
  fallbackUrl?: string;
}

export function RouteGuard({ children }: RouteGuardProps) {
  return <>{children}</>;
}

