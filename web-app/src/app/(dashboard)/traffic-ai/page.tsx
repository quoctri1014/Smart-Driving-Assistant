'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function TrafficAIPage() {
  const router = useRouter();

  useEffect(() => {
    // Đã hợp nhất module Giám sát AI vào trực tiếp trang Giám sát trực tiếp (/live)
    router.replace('/live');
  }, [router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-3">
      <div className="w-8 h-8 border-3 border-[#175CD3] border-t-transparent rounded-full animate-spin" />
      <p className="text-sm font-medium text-slate-600">
        Tính năng AI đã được tích hợp trực tiếp vào màn hình <strong>Giám sát trực tiếp</strong>.
      </p>
      <p className="text-xs text-slate-400">Đang tự động chuyển hướng...</p>
    </div>
  );
}
