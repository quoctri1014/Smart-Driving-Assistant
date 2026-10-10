import React from 'react';

export function TrafficGuardLogo({ size = 48, className = '' }: { size?: number; className?: string }) {
  const id = React.useId();

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient
          id={`tgShieldGrad-${id}`}
          x1="16"
          y1="8"
          x2="84"
          y2="92"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0%" stopColor="#1E6DEB" />
          <stop offset="50%" stopColor="#1A73E8" />
          <stop offset="100%" stopColor="#0B57D0" />
        </linearGradient>
      </defs>

      {/* 1. Shield Background */}
      <path
        d="M50 8C62 12.5 76 17 84 20C84 48 76 72 50 92C24 72 16 48 16 20C24 17 38 12.5 50 8Z"
        fill={`url(#tgShieldGrad-${id})`}
      />

      {/* 2. Top Roof / Skyline Cutout */}
      <path
        d="M24.5 30L50 20L75.5 27V33.5C64 34.5 48 36.5 24.5 46.5V30Z"
        fill="#FFFFFF"
      />

      {/* 3. Upper Curved Road Lane */}
      <path
        d="M23 71C26.5 54 39 42 75.5 37.5V44C46 48 33 58 28.5 78C26.5 76 24.5 73.5 23 71Z"
        fill="#FFFFFF"
      />

      {/* 4. Lower Curved Road Lane */}
      <path
        d="M37.5 86C41 71 51 56 75.5 48V54.5C57 61.5 48 73.5 44.5 89C42 88 39.5 87 37.5 86Z"
        fill="#FFFFFF"
      />
    </svg>
  );
}
