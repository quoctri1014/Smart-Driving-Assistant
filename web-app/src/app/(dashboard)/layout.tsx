'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AppSidebar } from '../../components/layout/AppSidebar';
import { AppHeader } from '../../components/layout/AppHeader';
import { useUiStore } from '../../stores/uiStore';
import { useAuthStore } from '../../stores/authStore';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isSidebarOpen } = useUiStore();
  const { checkAuth, isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    // If not authenticated, in a real app we'd redirect to /login.
    // However, since we might just want to show the UI even without backend,
    // let's just let it run or log for now. If you want strict auth, uncomment:
    /*
    if (!isAuthenticated) {
      router.push('/login');
    }
    */
  }, [isAuthenticated, router]);

  return (
    <div className="flex h-screen overflow-hidden bg-adas-bg">
      <AppSidebar />
      <div 
        className={`flex-1 flex flex-col transition-all duration-300 ${
          isSidebarOpen ? 'ml-64' : 'ml-20'
        }`}
      >
        <AppHeader />
        <main className="flex-1 overflow-auto p-6 relative">
          {children}
        </main>
      </div>
    </div>
  );
}
