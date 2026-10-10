'use client';

import React, { useEffect, Suspense } from 'react';
import { AppSidebar } from '../../components/layout/AppSidebar';
import { AppHeader } from '../../components/layout/AppHeader';
import { RouteGuard } from '../../components/auth/RouteGuard';
import { useUiStore } from '../../stores/uiStore';
import { useAuthStore } from '../../stores/authStore';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isSidebarOpen } = useUiStore();
  const { checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <div className="flex h-screen overflow-hidden bg-[#F6F8FA]">
      <Suspense fallback={<div className="w-16 h-screen bg-white border-r border-[#E4E9EF]" />}>
        <AppSidebar />
      </Suspense>
      <div
        className="flex-1 flex flex-col min-w-0 overflow-hidden transition-[margin-left] duration-250 ease-in-out"
        style={{
          marginLeft: isSidebarOpen ? '240px' : '64px',
        }}
      >
        <Suspense fallback={<div className="h-14 bg-white border-b border-[#E4E9EF]" />}>
          <AppHeader />
        </Suspense>
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-6 custom-scrollbar">
          <Suspense fallback={<div className="p-8 text-center text-xs text-[#667085]">Đang tải giao diện...</div>}>
            <RouteGuard>
              {children}
            </RouteGuard>
          </Suspense>
        </main>
      </div>
    </div>
  );
}
