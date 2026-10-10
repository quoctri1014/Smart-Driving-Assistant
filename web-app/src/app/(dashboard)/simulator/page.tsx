'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function SimulatorPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/live');
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="text-sm text-[#667085] flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-[#175CD3] animate-ping" />
        <span>Đang chuyển hướng sang Trợ lý Lái xe Live AI...</span>
      </div>
    </div>
  );
}
