import React from 'react';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
}

export function Badge({ 
  children, 
  variant = 'default',
  size = 'sm',
  className = '',
  ...props 
}: BadgeProps) {
  const variants = {
    default: 'bg-adas-surface text-adas-text-primary border border-adas-border',
    success: 'bg-adas-success/10 text-adas-success border border-adas-success/20',
    warning: 'bg-adas-warning/10 text-adas-warning border border-adas-warning/20',
    danger: 'bg-adas-danger/10 text-adas-danger border border-adas-danger/20',
    info: 'bg-adas-primary/10 text-adas-primary border border-adas-primary/20'
  };
  
  const sizes = {
    sm: 'px-2 py-0.5 text-xs font-semibold',
    md: 'px-2.5 py-1 text-sm font-semibold'
  };

  return (
    <span 
      className={`inline-flex items-center rounded-full whitespace-nowrap ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
