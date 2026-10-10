'use client';

import React from 'react';
import { Truck, Car, Bus, Navigation } from 'lucide-react';
import { TGSignalLine, SignalVariant } from './TGSignalLine';

export interface TGVehicleBadgeProps {
  plateNumber: string;
  type?: 'truck' | 'car' | 'bus' | 'other' | string;
  status?: SignalVariant;
  driverName?: string;
  className?: string;
}

export function TGVehicleBadge({
  plateNumber,
  type = 'truck',
  status = 'safe',
  driverName,
  className = '',
}: TGVehicleBadgeProps) {
  const getVehicleIcon = () => {
    switch (type.toLowerCase()) {
      case 'car':
        return <Car className="w-3.5 h-3.5 text-[#667085]" />;
      case 'bus':
        return <Bus className="w-3.5 h-3.5 text-[#667085]" />;
      case 'truck':
      default:
        return <Truck className="w-3.5 h-3.5 text-[#667085]" />;
    }
  };

  return (
    <div
      className={`inline-flex items-center gap-2 bg-[#F8FAFC] border border-[#D0D7DE] rounded-[6px] pl-2 pr-2.5 py-1 select-none shadow-[0_1px_2px_rgba(16,24,40,0.04)] ${className}`}
    >
      <TGSignalLine variant={status} placement="marker" size="sm" />

      <div className="flex items-center gap-1.5 border-r border-[#E4E9EF] pr-2">
        {getVehicleIcon()}
        <span className="font-bold text-xs text-[#16202A]">
          {plateNumber}
        </span>
      </div>

      {driverName && (
        <span className="text-[11px] text-[#667085] truncate max-w-[120px]">
          {driverName}
        </span>
      )}
    </div>
  );
}
