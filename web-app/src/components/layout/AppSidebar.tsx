import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  MonitorPlay, 
  Car, 
  Route, 
  AlertOctagon, 
  BarChart3, 
  Cpu,
  Server,
  Bell,
  Settings,
  ChevronLeft
} from 'lucide-react';
import { useUiStore } from '../../stores/uiStore';

const MAIN_NAV = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Live Monitor', href: '/live', icon: MonitorPlay },
  { name: 'Simulator', href: '/simulator', icon: Car },
];

const DATA_NAV = [
  { name: 'Journeys', href: '/journeys', icon: Route },
  { name: 'Violations', href: '/violations', icon: AlertOctagon },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
];

const SYSTEM_NAV = [
  { name: 'AI Engine', href: '/ai-status', icon: Cpu },
  { name: 'Devices', href: '/devices', icon: Server },
  { name: 'Notifications', href: '/notifications', icon: Bell },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { isSidebarOpen, toggleSidebar } = useUiStore();

  const renderLinks = (links: typeof MAIN_NAV) => {
    return links.map((link) => {
      const isActive = pathname === link.href || pathname?.startsWith(`${link.href}/`);
      const Icon = link.icon;
      
      return (
        <Link 
          key={link.href}
          href={link.href}
          className={`flex items-center gap-3 px-3 py-2 rounded-xl transition-colors ${
            isActive 
              ? 'bg-adas-primary/10 text-adas-primary font-medium' 
              : 'text-adas-text-secondary hover:text-adas-text-primary hover:bg-adas-surface'
          }`}
          title={!isSidebarOpen ? link.name : undefined}
        >
          <Icon className={`shrink-0 ${isActive ? 'text-adas-primary' : 'text-adas-text-muted'} ${isSidebarOpen ? 'w-5 h-5' : 'w-6 h-6 mx-auto'}`} />
          {isSidebarOpen && <span>{link.name}</span>}
        </Link>
      );
    });
  };

  return (
    <aside 
      className={`fixed top-0 left-0 z-40 h-screen transition-all duration-300 border-r border-adas-border bg-adas-bg flex flex-col ${
        isSidebarOpen ? 'w-64' : 'w-20'
      }`}
    >
      <div className="flex h-16 items-center justify-between px-4 border-b border-adas-border/50 shrink-0">
        {isSidebarOpen && (
          <div className="flex items-center gap-2 font-bold text-lg text-adas-text-primary">
            <div className="w-8 h-8 rounded-lg bg-adas-primary flex items-center justify-center text-white shrink-0">
              <Car className="w-5 h-5" />
            </div>
            <span className="truncate">Smart ADAS</span>
          </div>
        )}
        {!isSidebarOpen && (
          <div className="w-8 h-8 mx-auto rounded-lg bg-adas-primary flex items-center justify-center text-white shrink-0">
            <Car className="w-5 h-5" />
          </div>
        )}
        
        {isSidebarOpen && (
          <button 
            onClick={toggleSidebar}
            className="p-1 rounded-lg hover:bg-adas-surface text-adas-text-muted transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto py-4 px-3 flex flex-col gap-6 custom-scrollbar">
        <div>
          {isSidebarOpen && <h3 className="px-3 mb-2 text-xs font-semibold text-adas-text-muted uppercase tracking-wider">Main</h3>}
          <nav className="flex flex-col gap-1">{renderLinks(MAIN_NAV)}</nav>
        </div>

        <div>
          {isSidebarOpen && <h3 className="px-3 mb-2 text-xs font-semibold text-adas-text-muted uppercase tracking-wider">Data</h3>}
          <nav className="flex flex-col gap-1">{renderLinks(DATA_NAV)}</nav>
        </div>

        <div>
          {isSidebarOpen && <h3 className="px-3 mb-2 text-xs font-semibold text-adas-text-muted uppercase tracking-wider">System</h3>}
          <nav className="flex flex-col gap-1">{renderLinks(SYSTEM_NAV)}</nav>
        </div>
      </div>

      <div className="p-4 border-t border-adas-border/50 shrink-0">
        {!isSidebarOpen && (
           <button 
             onClick={toggleSidebar}
             className="w-full py-2 flex justify-center text-adas-text-muted hover:text-adas-text-primary"
           >
             <ChevronLeft className="w-6 h-6 rotate-180" />
           </button>
        )}
        {isSidebarOpen && (
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-adas-surface border border-adas-border flex items-center justify-center">
              <span className="text-sm font-medium">AD</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-adas-text-primary truncate">Admin User</p>
              <p className="text-xs text-adas-text-muted truncate">admin@adas.local</p>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
