import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-2xl text-center">
        <div className="mb-6 inline-block bg-blue-100 text-blue-700 px-4 py-1.5 rounded-full text-sm font-bold tracking-wide uppercase">
          Smart Driving Assistant
        </div>
        <h1 className="text-5xl md:text-6xl font-black text-slate-800 tracking-tight leading-tight mb-6">
          Hệ thống AI giám sát <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-500">
            an toàn giao thông
          </span>
        </h1>
        <p className="text-lg text-slate-500 mb-10 max-w-xl mx-auto leading-relaxed">
          Nền tảng tích hợp nhận diện biển số, phát hiện va chạm và giám sát trạng thái tài xế (buồn ngủ, dây an toàn) theo thời gian thực.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link 
            href="/live-demo" 
            className="w-full sm:w-auto px-8 py-4 bg-slate-900 text-white rounded-full font-bold text-lg hover:bg-slate-800 transition-all hover:scale-105 active:scale-95 shadow-lg shadow-slate-900/20"
          >
            Chạy Live Demo (Webcam)
          </Link>
          <Link 
            href="/dashboard" 
            className="w-full sm:w-auto px-8 py-4 bg-white text-slate-700 border-2 border-slate-200 rounded-full font-bold text-lg hover:border-slate-300 hover:bg-slate-50 transition-all active:scale-95"
          >
            Vào Dashboard Quản trị
          </Link>
        </div>
      </div>
    </main>
  );
}
