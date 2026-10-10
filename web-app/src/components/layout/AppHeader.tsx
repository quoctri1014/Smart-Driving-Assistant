'use client';

import React, { useEffect, useState, useRef } from 'react';
import { usePathname } from 'next/navigation';
import {
  Menu,
  Clock,
  ChevronRight,
  ChevronDown,
  Volume2,
  VolumeX,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { useUiStore } from '../../stores/uiStore';
import { useAuthStore } from '../../stores/authStore';
import { TGUserAvatar } from '../ui/TGUserAvatar';
import { NotificationBellPopover } from '../notifications/NotificationBellPopover';
import { soundEngine } from '../../lib/soundEngine';

const PAGE_METADATA: Record<string, { title: string; section: string }> = {
  '/dashboard': { title: 'Bảng Điều Khiển Cá Nhân', section: 'Tổng Quan' },
  '/live': { title: 'Trợ Lý Lái Xe Thời Gian Thực', section: 'Camera AI' },
  '/simulator': { title: 'Phòng Mô Phỏng Thử Nghiệm', section: 'Công Cụ' },
  '/journeys': { title: 'Nhật Ký Hành Trình', section: 'Lịch Sử' },
  '/violations': { title: 'Lịch Sử Cảnh Báo An Toàn', section: 'An Toàn' },
  '/analytics': { title: 'Báo Cáo An Toàn Cá Nhân', section: 'Thống Kê' },
  '/ai-status': { title: '12 Module AI Thị Giác', section: 'Công Nghệ AI' },
  '/devices': { title: 'Thiết Bị Cảm Biến', section: 'Phần Cứng' },
  '/settings': { title: 'Cài Đặt Trợ Lý', section: 'Tùy Chọn' },
};

export function AppHeader() {
  const { toggleSidebar } = useUiStore();
  const { user } = useAuthStore();
  const pathname = usePathname();

  const [apiStatus, setApiStatus] = useState<'online' | 'offline'>('online');
  const [currentTime, setCurrentTime] = useState<string>('');
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const currentMeta = PAGE_METADATA[pathname] || {
    title: 'Trợ Lý Lái Xe',
    section: 'Cá Nhân',
  };

  // Click outside to close user menu
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString('vi-VN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })
      );
    };
    updateClock();
    const t = setInterval(updateClock, 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    let mounted = true;
    const checkBackend = async () => {
      try {
        const res = await fetch('http://localhost:8000/health').catch(() => null);
        if (mounted) {
          setApiStatus(res && res.ok ? 'online' : 'offline');
        }
      } catch {
        if (mounted) setApiStatus('offline');
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleToggleSound = () => {
    const nextMuted = soundEngine.toggleMuted();
    setIsAudioMuted(nextMuted);
    if (!nextMuted) {
      soundEngine.testVoice();
    } else {
      soundEngine.speak('Đã tắt cảnh báo âm thanh', 'normal');
    }
  };

  const handleTestVoice = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsAudioMuted(false);
    soundEngine.testVoice();
  };

  return (
    <header className="h-14 border-b border-[#E4E9EF] bg-white flex items-center justify-between px-5 sticky top-0 z-30 shrink-0 select-none shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
      {/* Left: Sidebar Toggle + Title & Breadcrumb */}
      <div className="flex items-center gap-3 shrink-0 whitespace-nowrap">
        <button
          onClick={toggleSidebar}
          aria-label="Menu"
          className="p-1.5 rounded-[6px] text-[#667085] hover:text-[#16202A] hover:bg-[#F1F4F7] transition-colors shrink-0 cursor-pointer"
        >
          <Menu className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2 text-sm whitespace-nowrap shrink-0">
          <span className="text-[#667085] font-normal hidden sm:inline">
            {currentMeta.section}
          </span>
          <ChevronRight className="w-3.5 h-3.5 text-[#D0D7DE] hidden sm:inline shrink-0" />
          <span className="font-semibold text-[#16202A] tracking-tight whitespace-nowrap">
            {currentMeta.title}
          </span>
        </div>
      </div>

      {/* Right Toolbar */}
      <div className="flex items-center gap-3.5">
        {/* Quick Audio Warning Toggle & Voice Test Button */}
        <div className="flex items-center gap-1 bg-[#F8FAFC] border border-[#E4E9EF] p-0.5 rounded-[8px]">
          <button
            type="button"
            onClick={handleToggleSound}
            title={isAudioMuted ? 'Âm thanh cảnh báo đang tắt. Nhấn để bật' : 'Âm thanh cảnh báo đang bật. Nhấn để tắt'}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] text-xs font-semibold transition-all cursor-pointer ${
              isAudioMuted
                ? 'bg-[#FEF3F2] border border-[#FECDCA] text-[#D92D20]'
                : 'bg-[#ECFDF3] border border-[#ABEFC6] text-[#079455]'
            }`}
          >
            {isAudioMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">{isAudioMuted ? 'Đã tắt tiếng' : 'Cảnh báo giọng nói'}</span>
          </button>

          <button
            type="button"
            onClick={handleTestVoice}
            title="Thử phát giọng nói cảnh báo tiếng Việt và kiểm tra loa ngay"
            className="px-2.5 py-1 rounded-[6px] text-[11px] font-bold text-[#175CD3] hover:bg-[#EFF8FF] transition-colors cursor-pointer flex items-center gap-1 bg-white border border-[#B2DDFF] shadow-2xs"
          >
            <span>📢 Thử giọng</span>
          </button>
        </div>

        <div className="hidden md:block w-px h-4 bg-[#E4E9EF]" />

        {/* Real-time Clock */}
        <div className="hidden md:flex items-center gap-1.5 text-xs font-mono text-[#667085]">
          <Clock className="w-3.5 h-3.5 text-[#98A2B3]" />
          <span>{currentTime || '00:00:00'}</span>
        </div>

        <div className="hidden sm:block w-px h-4 bg-[#E4E9EF]" />

        {/* Server Status */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              apiStatus === 'online' ? 'bg-[#12B76A] ring-4 ring-[#ECFDF3]' : 'bg-[#F04438] ring-4 ring-[#FEF3F2]'
            }`}
          />
          <span className="font-medium text-[#475467]">
            {apiStatus === 'online' ? 'AI Sẵn sàng' : 'Chưa kết nối AI'}
          </span>
        </div>

        {/* Notification Center Popover */}
        <NotificationBellPopover />

        {/* Personal User Menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 pl-1.5 pr-2 py-1 rounded-[8px] bg-white hover:bg-[#F8FAFC] border border-[#D0D7DE] text-xs transition-colors shadow-[0_1px_2px_rgba(16,24,40,0.04)] cursor-pointer"
          >
            <TGUserAvatar
              name={user?.full_name || 'Người Lái Xe'}
              role="ENTERPRISE_ADMIN"
              size="sm"
            />
            <div className="text-left hidden sm:block">
              <span className="font-semibold text-[#16202A] block text-xs leading-tight">
                {user?.full_name || 'Người Lái Xe'}
              </span>
              <span className="text-[10px] text-[#175CD3] font-medium block leading-tight">
                Chế độ Cá nhân
              </span>
            </div>

            <ChevronDown className="w-3 h-3 text-[#667085]" />
          </button>

          {/* User Popover */}
          {showUserMenu && (
            <div className="absolute right-0 top-12 w-64 bg-white border border-[#E4E9EF] rounded-[10px] shadow-[0_12px_24px_-4px_rgba(16,24,40,0.12),0_4px_6px_-2px_rgba(16,24,40,0.05)] py-2 z-50 select-none animate-in fade-in zoom-in-95 duration-100">
              <div className="px-4 py-3 border-b border-[#E4E9EF] bg-[#F8FAFC]">
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#175CD3]" />
                  <span className="font-bold text-xs text-[#16202A]">Trợ Lý Lái Xe Cá Nhân</span>
                </div>
                <div className="text-[11px] text-[#667085] mt-1">
                  Đang hoạt động trên thiết bị của bạn
                </div>
              </div>

              <div className="p-2 space-y-1 text-xs text-[#344054]">
                <div className="flex items-center justify-between px-2.5 py-1.5 rounded-[6px] hover:bg-[#F8FAFC]">
                  <span className="text-[#667085]">Phiên bản:</span>
                  <span className="font-semibold text-[#16202A]">Personal v2.5</span>
                </div>
                <div className="flex items-center justify-between px-2.5 py-1.5 rounded-[6px] hover:bg-[#F8FAFC]">
                  <span className="text-[#667085]">Điểm an toàn:</span>
                  <span className="font-bold text-[#17B26A]">98 / 100</span>
                </div>
                <div className="flex items-center justify-between px-2.5 py-1.5 rounded-[6px] hover:bg-[#F8FAFC]">
                  <span className="text-[#667085]">Cảm biến Camera:</span>
                  <span className="font-medium text-[#175CD3]">2 Kênh (Đường & Cabin)</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

