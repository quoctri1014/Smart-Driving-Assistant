'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Video,
  History,
  AlertTriangle,
  Cpu,
  ChevronLeft,
  ChevronRight,
  type LucideIcon,
} from 'lucide-react';
import { useUiStore } from '../../stores/uiStore';
import { TGSignalLine } from '../ui/TGSignalLine';
import { TGStatusBadge } from '../ui/TGStatusBadge';
import { TrafficGuardLogo } from '../ui/TrafficGuardLogo';

interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
  badge?: string | number;
  badgeVariant?: 'safe' | 'warning' | 'critical' | 'info' | 'primary';
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export function AppSidebar() {
  const pathname = usePathname();
  const { isSidebarOpen, toggleSidebar } = useUiStore();

  const sections: NavSection[] = [
    {
      title: 'TRỢ LÝ THỜI GIAN THỰC',
      items: [
        {
          name: 'Trợ lý Lái xe (Live AI)',
          href: '/live',
          icon: Video,
          badge: 'AI Live',
          badgeVariant: 'safe',
        },
        {
          name: 'Bảng điều khiển cá nhân',
          href: '/dashboard',
          icon: LayoutDashboard,
        },
      ],
    },
    {
      title: 'HỒ SƠ & NHẬT KÝ',
      items: [
        {
          name: 'Nhật ký hành trình',
          href: '/journeys',
          icon: History,
        },
        {
          name: 'Cảnh báo an toàn',
          href: '/violations',
          icon: AlertTriangle,
        },
      ],
    },
    {
      title: 'CÔNG CỤ & CÔNG NGHỆ',
      items: [
        {
          name: '12 Module AI Thị giác',
          href: '/ai-status',
          icon: Cpu,
        },
      ],
    },
  ];

  const isItemActive = (href: string) => {
    return pathname === href;
  };

  return (
    <aside
      className={`fixed top-0 left-0 z-40 h-screen bg-white border-r border-[#E4E9EF] flex flex-col transition-[width] duration-200 select-none shadow-[1px_0_3px_rgba(16,24,40,0.03)] ${
        isSidebarOpen ? 'w-60' : 'w-16'
      }`}
    >
      {/* Brand Header */}
      <div className="h-14 flex items-center justify-between px-3.5 border-b border-[#E4E9EF] shrink-0 bg-white">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <TrafficGuardLogo size={28} className="shrink-0" />
          {isSidebarOpen && (
            <div className="flex flex-col truncate">
              <span className="text-xs font-extrabold text-[#16202A] tracking-wider truncate">
                DRIVING<span className="text-[#175CD3]">ASSISTANT</span>
              </span>
              <span className="text-[10px] text-[#175CD3] font-semibold truncate">
                Trợ lý lái xe cá nhân
              </span>
            </div>
          )}
        </div>

        {isSidebarOpen && (
          <button
            onClick={toggleSidebar}
            id="sidebar-toggle"
            aria-label="Thu gọn thanh điều hướng"
            className="p-1 rounded-[6px] text-[#667085] hover:text-[#16202A] hover:bg-[#F1F4F7] transition-colors cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4 custom-scrollbar">
        {sections.map((section, sIdx) => {
          return (
            <div key={sIdx} className="space-y-1">
              {/* Section Header */}
              {isSidebarOpen ? (
                <div className="px-3 py-1 text-[10px] font-bold tracking-wider text-[#98A2B3] uppercase">
                  {section.title}
                </div>
              ) : (
                <div className="my-1 border-t border-[#F1F4F7]" />
              )}

              {/* Section Items */}
              {section.items.map((item) => {
                const isActive = isItemActive(item.href);
                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={!isSidebarOpen ? `${section.title}: ${item.name}` : undefined}
                    className={`relative flex items-center gap-2.5 px-3 py-2 rounded-[8px] text-xs font-semibold transition-all duration-150 group ${
                      !isSidebarOpen ? 'justify-center px-2' : 'justify-start'
                    } ${
                      isActive
                        ? 'bg-[#EFF4FF] text-[#175CD3] font-bold shadow-[0_1px_2px_rgba(23,92,211,0.06)]'
                        : 'text-[#667085] hover:text-[#16202A] hover:bg-[#F1F4F7]'
                    }`}
                  >
                    {isActive && (
                      <span className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-[#175CD3] rounded-r-full" />
                    )}

                    <Icon
                      className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-105 ${
                        isActive ? 'text-[#175CD3]' : 'text-[#667085]'
                      }`}
                    />

                    {isSidebarOpen && (
                      <span className="truncate flex-1">{item.name}</span>
                    )}

                    {isSidebarOpen && item.badge && (
                      <TGStatusBadge
                        variant={item.badgeVariant || 'info'}
                        size="sm"
                        showIcon={false}
                        className="text-[9px] px-1.5 py-0 font-bold ml-auto"
                      >
                        {item.badge}
                      </TGStatusBadge>
                    )}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </div>

      {/* Footer Status */}
      <div className="p-3 border-t border-[#E4E9EF] shrink-0 bg-[#F8FAFC]">
        {isSidebarOpen ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <TGSignalLine variant="safe" placement="marker" size="sm" />
              <span className="text-[11px] text-[#667085] font-medium">Bảo vệ cá nhân</span>
            </div>
            <TGStatusBadge
              variant="safe"
              size="sm"
              showIcon={false}
              className="text-[9px] font-bold"
            >
              Trực tuyến
            </TGStatusBadge>
          </div>
        ) : (
          <button
            onClick={toggleSidebar}
            aria-label="Mở rộng thanh điều hướng"
            className="w-full flex justify-center py-1 text-[#667085] hover:text-[#16202A] cursor-pointer"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </aside>
  );
}

