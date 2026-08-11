import React, { useEffect, useState } from 'react';
import { Menu, Activity, Wifi, WifiOff } from 'lucide-react';
import { useUiStore } from '../../stores/uiStore';
import { apiClient } from '../../services/apiClient';

export function AppHeader() {
  const { toggleSidebar } = useUiStore();
  const [apiStatus, setApiStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  
  // Fake or basic ping to check backend status. 
  // In a real app we might ping a health endpoint. 
  // For now, let's just attempt to hit the base API url or a known endpoint occasionally.
  useEffect(() => {
    let mounted = true;
    
    const checkStatus = async () => {
      try {
        // Just checking if we can resolve the host/api
        await apiClient.get('/api/auth/login', { method: 'OPTIONS' });
        if (mounted) setApiStatus('online');
      } catch (e) {
        if (mounted) setApiStatus('offline');
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="h-16 border-b border-adas-border bg-adas-bg/80 backdrop-blur-md flex items-center justify-between px-4 sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <button 
          onClick={toggleSidebar}
          className="lg:hidden p-2 -ml-2 rounded-lg hover:bg-adas-surface text-adas-text-muted"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="font-semibold text-adas-text-primary hidden sm:block">
          Smart Driving Assistant
        </h1>
      </div>

      <div className="flex items-center gap-4">
        {/* API Status Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-adas-surface border border-adas-border text-xs font-medium">
          <Activity className="w-4 h-4 text-adas-text-muted" />
          <span className="text-adas-text-secondary">Backend API:</span>
          {apiStatus === 'checking' ? (
            <span className="text-adas-text-muted flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-adas-text-muted animate-pulse" /> Checking
            </span>
          ) : apiStatus === 'online' ? (
            <span className="text-adas-success flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-adas-success shadow-[0_0_8px_rgba(34,197,94,0.5)]" /> Online
            </span>
          ) : (
            <span className="text-adas-danger flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-adas-danger" /> Offline
            </span>
          )}
        </div>
      </div>
    </header>
  );
}
