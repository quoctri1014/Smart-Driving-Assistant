'use client';

import React, { useEffect, useState, useRef } from 'react';
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldAlert,
  Clock,
  ExternalLink,
  Check
} from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import { TGStatusBadge } from '../ui/TGStatusBadge';

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO' | 'SAFE' | 'SYSTEM';
  is_read: boolean;
  read_at?: string | null;
  acknowledged_at?: string | null;
  resource_type?: string;
  resource_id?: number;
  created_at: string;
}

export function NotificationBellPopover() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = async () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) return;
    try {
      const data = await apiClient.get<NotificationItem[]>('/api/v1/notifications?limit=8');
      if (Array.isArray(data)) {
        setNotifications(data);
      }
    } catch {
      // Quietly ignore in unauthorized / offline mode
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkRead = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.patch(`/api/v1/notifications/${id}/read`, {});
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n))
      );
    } catch (err) {
      console.warn('Mark read error', err);
    }
  };

  const handleAcknowledge = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.patch(`/api/v1/notifications/${id}/acknowledge`, {});
      setNotifications((prev) =>
        prev.map((n) =>
          n.id === id
            ? { ...n, is_read: true, read_at: new Date().toISOString(), acknowledged_at: new Date().toISOString() }
            : n
        )
      );
    } catch (err) {
      console.warn('Acknowledge error', err);
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="relative" ref={popoverRef}>
      {/* Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg text-[#667085] hover:text-[#16202A] hover:bg-[#F1F4F7] transition-colors"
        aria-label="Thông báo hệ thống"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex items-center justify-center min-w-[16px] h-4 px-1 rounded-full bg-[#F04438] text-[10px] font-bold text-white font-mono">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Popover Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-[#FFFFFF] border border-[#E4E9EF] rounded-xl shadow-xl z-50 overflow-hidden animate-in fade-in duration-150">
          <div className="p-3 bg-[#F8FAFC] border-b border-[#E4E9EF] flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold text-[#16202A]">Thông Báo Hệ Thống</span>
              {unreadCount > 0 && (
                <span className="px-1.5 py-0.2 rounded-full bg-[#175CD3]/10 text-[#175CD3] text-[10px] font-bold">
                  {unreadCount} mới
                </span>
              )}
            </div>
            <span className="text-[11px] text-[#667085]">Thời gian thực</span>
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-[#E4E9EF]">
            {notifications.length === 0 ? (
              <div className="p-6 text-center text-xs text-[#98A2B3]">
                <CheckCircle2 className="w-6 h-6 mx-auto text-[#17B26A]/50 mb-1" />
                <p>Không có thông báo nào mới</p>
              </div>
            ) : (
              notifications.map((n) => {
                const sevVariant = n.severity === 'CRITICAL' ? 'critical' : n.severity === 'WARNING' ? 'warning' : 'info';

                return (
                  <div
                    key={n.id}
                    className={`p-3 text-xs transition-colors hover:bg-[#F8FAFC] ${
                      !n.is_read ? 'bg-[#175CD3]/[0.03]' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <TGStatusBadge variant={sevVariant} size="sm">
                          {n.severity === 'CRITICAL' ? 'Khẩn cấp' : n.severity === 'WARNING' ? 'Cảnh báo' : 'Thông tin'}
                        </TGStatusBadge>
                        <span className="font-semibold text-[#16202A] text-xs truncate max-w-[180px]">{n.title}</span>
                      </div>
                      <span className="text-[10px] text-[#98A2B3] font-mono shrink-0">
                        {n.created_at?.split('T')[1]?.substring(0, 5) || 'Vừa xong'}
                      </span>
                    </div>

                    <p className="text-[#667085] text-xs mt-1 leading-relaxed">{n.message}</p>

                    <div className="flex items-center justify-between mt-2 pt-1">
                      {n.acknowledged_at ? (
                        <span className="text-[10px] text-[#17B26A] font-semibold flex items-center gap-1">
                          <Check className="w-3 h-3" />
                          Đã tiếp nhận
                        </span>
                      ) : n.severity === 'CRITICAL' ? (
                        <button
                          onClick={(e) => handleAcknowledge(n.id, e)}
                          className="px-2 py-0.5 rounded bg-[#F04438] text-white text-[10px] font-bold hover:bg-[#D92D20] transition-colors"
                        >
                          Tiếp nhận ngay
                        </button>
                      ) : (
                        <span />
                      )}

                      {!n.is_read && (
                        <button
                          onClick={(e) => handleMarkRead(n.id, e)}
                          className="text-[11px] text-[#175CD3] hover:underline"
                        >
                          Đã đọc
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
