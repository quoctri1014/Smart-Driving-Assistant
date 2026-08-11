import React from 'react';
import { AlertTriangle, Info, CheckCircle2, XCircle } from 'lucide-react';

interface AlertBannerProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'warning' | 'danger' | 'success';
  title?: string;
  onDismiss?: () => void;
}

export function AlertBanner({ 
  children, 
  variant = 'info',
  title,
  className = '',
  onDismiss,
  ...props 
}: AlertBannerProps) {
  const styles = {
    info: {
      bg: 'bg-adas-primary/10',
      border: 'border-adas-primary/20',
      icon: <Info className="h-5 w-5 text-adas-primary" />,
      text: 'text-adas-text-primary'
    },
    warning: {
      bg: 'bg-adas-warning/10',
      border: 'border-adas-warning/20',
      icon: <AlertTriangle className="h-5 w-5 text-adas-warning" />,
      text: 'text-adas-text-primary'
    },
    danger: {
      bg: 'bg-adas-danger/10',
      border: 'border-adas-danger/20',
      icon: <XCircle className="h-5 w-5 text-adas-danger" />,
      text: 'text-adas-text-primary'
    },
    success: {
      bg: 'bg-adas-success/10',
      border: 'border-adas-success/20',
      icon: <CheckCircle2 className="h-5 w-5 text-adas-success" />,
      text: 'text-adas-text-primary'
    }
  };

  const currentStyle = styles[variant];

  return (
    <div 
      className={`rounded-xl border p-4 flex gap-3 ${currentStyle.bg} ${currentStyle.border} ${className}`}
      role="alert"
      {...props}
    >
      <div className="shrink-0 mt-0.5">
        {currentStyle.icon}
      </div>
      <div className="flex-1">
        {title && <h4 className={`font-semibold mb-1 ${currentStyle.text}`}>{title}</h4>}
        <div className="text-sm text-adas-text-secondary">
          {children}
        </div>
      </div>
      {onDismiss && (
        <button 
          onClick={onDismiss}
          className="shrink-0 ml-4 text-adas-text-muted hover:text-adas-text-primary transition-colors"
          aria-label="Dismiss"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      )}
    </div>
  );
}
