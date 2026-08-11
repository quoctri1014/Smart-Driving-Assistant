import React from 'react';

export default function PhoneFrameWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900 p-4">
      {/* Phone container */}
      <div className="relative w-[375px] h-[812px] bg-black rounded-[50px] shadow-2xl overflow-hidden border-[12px] border-gray-800">
        
        {/* Fake Notch */}
        <div className="absolute top-0 inset-x-0 h-6 flex justify-center z-50">
          <div className="w-32 h-6 bg-black rounded-b-2xl"></div>
        </div>

        {/* Content */}
        <div className="w-full h-full bg-slate-100 flex flex-col relative overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
