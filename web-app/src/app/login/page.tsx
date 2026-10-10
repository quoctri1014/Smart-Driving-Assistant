'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/dashboard');
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0F172A] text-white">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-[#1A73E8] border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium text-[#94A3B8]">Đang chuyển hướng vào Trợ Lý Lái Xe...</p>
      </div>
    </div>
  );
}

