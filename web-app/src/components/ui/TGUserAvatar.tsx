'use client';

import React from 'react';
import { User } from 'lucide-react';
import { SignalVariant } from './TGSignalLine';

export interface TGUserAvatarProps {
  name?: string;
  role?: 'admin' | 'dispatcher' | 'driver' | string;
  status?: SignalVariant;
  size?: 'sm' | 'md' | 'lg';
  avatarUrl?: string;
  className?: string;
}

const AVATAR_SIZES = {
  sm: 'w-7 h-7 text-[10px]',
  md: 'w-9 h-9 text-xs',
  lg: 'w-11 h-11 text-sm',
};

const STATUS_DOT_COLORS: Record<string, string> = {
  safe: 'bg-[#17B26A]',
  success: 'bg-[#17B26A]',
  warning: 'bg-[#F79009]',
  critical: 'bg-[#F04438]',
  danger: 'bg-[#F04438]',
  info: 'bg-[#2E90FA]',
  primary: 'bg-[#175CD3]',
  neutral: 'bg-[#98A2B3]',
  default: 'bg-[#98A2B3]',
};

export function TGUserAvatar({
  name,
  role,
  status,
  size = 'md',
  avatarUrl,
  className = '',
}: TGUserAvatarProps) {
  const getInitials = (text?: string) => {
    if (!text) return 'TG';
    const parts = text.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  const getRoleBg = () => {
    if (role === 'admin' || role === 'ENTERPRISE_ADMIN') {
      return 'bg-[#175CD3] text-white';
    }
    if (role === 'dispatcher' || role === 'FLEET_DISPATCHER') {
      return 'bg-[#0E9384] text-white';
    }
    if (role === 'driver' || role === 'FLEET_DRIVER') {
      return 'bg-[#F1F4F7] text-[#16202A] border border-[#E4E9EF]';
    }
    return 'bg-[#F1F4F7] text-[#16202A] border border-[#E4E9EF]';
  };

  return (
    <div className={`relative inline-flex shrink-0 ${className}`}>
      {avatarUrl ? (
        <img
          src={avatarUrl}
          alt={name || 'User avatar'}
          className={`${AVATAR_SIZES[size]} rounded-full object-cover border border-[#E4E9EF]`}
        />
      ) : (
        <div
          className={`${AVATAR_SIZES[size]} rounded-full flex items-center justify-center font-bold select-none ${getRoleBg()}`}
        >
          {name ? getInitials(name) : <User className="w-4 h-4" />}
        </div>
      )}

      {status && (
        <span
          className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full ring-2 ring-white ${
            STATUS_DOT_COLORS[status] || STATUS_DOT_COLORS.neutral
          }`}
          aria-hidden="true"
        />
      )}
    </div>
  );
}
