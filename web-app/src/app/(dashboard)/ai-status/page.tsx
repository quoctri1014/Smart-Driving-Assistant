'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '../../../services/apiClient';
import {
  TGCard,
  TGCardHeader,
  TGCardTitle,
  TGCardContent,
  TGStatusBadge,
} from '../../../components/ui';
import {
  Cpu,
  BarChart2,
  CheckCircle2,
  Clock,
  Layers,
  Terminal,
  Activity,
  AlertCircle,
  ShieldCheck,
} from 'lucide-react';

interface BenchmarkRealData {
  status: string;
  has_real_data: boolean;
  video_tested?: string;
  frames_evaluated?: number;
  total_duration_seconds?: number;
  fps_achieved?: number;
  overall_latency_ms?: number;
  latency_min_ms?: number;
  latency_max_ms?: number;
  unique_objects_tracked?: number;
  evaluation_with_ground_truth?: boolean;
  metrics?: {
    precision: string;
    recall: string;
    f1_score: string;
    true_positives?: number | null;
    false_positives?: number | null;
    false_negatives?: number | null;
  };
  timestamp?: string;
  message?: string;
}

interface AIStatusResponse {
  models: { name: string; loaded: boolean }[];
  fps: number | null;
  latency_ms: number | null;
  benchmark?: BenchmarkRealData;
}

export default function AIStatusPage() {
  const [data, setData] = useState<AIStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    apiClient
      .get<AIStatusResponse>('/api/fleet/ai-status')
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto select-none">
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#16202A] tracking-tight">
            Giám Sát Hệ Thống AI Thị Giác
          </h1>
          <p className="text-sm text-[#475467] mt-1">
            Trạng thái tải bộ nhớ của các mô-đun AI và báo cáo kiểm chuẩn thực nghiệm trên video thật
          </p>
        </div>

        {data?.benchmark?.has_real_data && (
          <div className="flex items-center gap-3">
            <div className="bg-white border border-[#E4E9EF] px-4 py-2 rounded-xl text-center shadow-xs">
              <span className="text-xs text-[#667085] block font-medium">FPS ĐO THẬT</span>
              <span className="text-lg font-bold text-[#0E9384] font-mono">{data.benchmark.fps_achieved} FPS</span>
            </div>
            <div className="bg-white border border-[#E4E9EF] px-4 py-2 rounded-xl text-center shadow-xs">
              <span className="text-xs text-[#667085] block font-medium">ĐỘ TRỄ TRUNG BÌNH</span>
              <span className="text-lg font-bold text-[#175CD3] font-mono">{data.benchmark.overall_latency_ms} ms</span>
            </div>
          </div>
        )}
      </div>

      {error ? (
        <div className="p-4 rounded-xl bg-[#FEF3F2] border border-[#FECDCA] text-sm text-[#B42318] flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>Không thể kết nối đến máy chủ AI backend. Vui lòng kiểm tra cổng 8000 và phiên đăng nhập.</span>
        </div>
      ) : loading ? (
        <div className="py-16 text-center text-sm text-[#667085]">Đang kiểm tra trạng thái hệ thống AI...</div>
      ) : (
        <>
          {/* 2. Trạng thái 12 Module AI */}
          <TGCard variant="default">
            <TGCardHeader className="pb-3 border-b border-[#E4E9EF]">
              <TGCardTitle className="text-base font-bold text-[#16202A] flex items-center gap-2">
                <Cpu className="w-4 h-4 text-[#175CD3]" />
                Trạng Thái Bộ Nhớ Các Mô-đun AI
              </TGCardTitle>
            </TGCardHeader>

            <TGCardContent className="pt-4">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {data?.models.map((m) => (
                  <div
                    key={m.name}
                    className="p-3.5 rounded-lg bg-[#F8FAFC] border border-[#E4E9EF] flex items-center justify-between hover:border-[#B2CCFF] transition-colors"
                  >
                    <span className="text-sm font-medium text-[#16202A]">{m.name}</span>
                    <TGStatusBadge variant={m.loaded ? 'safe' : 'warning'} size="sm">
                      {m.loaded ? 'Đã tải' : 'Chưa nạp'}
                    </TGStatusBadge>
                  </div>
                ))}
              </div>
            </TGCardContent>
          </TGCard>

          {/* 3. Khu Vực Kiểm Chuẩn Thực Tế (Benchmark Results) */}
          <TGCard variant="default">
            <TGCardHeader className="pb-3 border-b border-[#E4E9EF]">
              <TGCardTitle className="text-base font-bold text-[#16202A] flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-[#175CD3]" />
                Kết Quả Kiểm Chuẩn Thực Nghiệm
              </TGCardTitle>
            </TGCardHeader>

            <TGCardContent className="pt-4">
              {data?.benchmark?.has_real_data ? (
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E4E9EF]">
                    <div>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#ECFDF3] text-[#027A48] border border-[#A6F4C5] uppercase">
                        Dữ Liệu Đo Kiểm Thật
                      </span>
                      <h3 className="text-base font-bold text-[#16202A] mt-2">
                        Video: {data.benchmark.video_tested} ({data.benchmark.frames_evaluated} frames)
                      </h3>
                      <p className="text-xs text-[#667085] mt-0.5">
                        Thời điểm đo: {data.benchmark.timestamp} | Thời lượng chạy: {data.benchmark.total_duration_seconds}s
                      </p>
                    </div>
                    <div className="text-left sm:text-right">
                      <span className="text-xs text-[#667085] block">Phương tiện đã bám vết (Tracked IDs)</span>
                      <span className="text-2xl font-bold text-[#16202A] font-mono">{data.benchmark.unique_objects_tracked}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
                    <div className="p-3.5 rounded-lg bg-[#F8FAFC] border border-[#E4E9EF]">
                      <span className="text-xs text-[#667085] block">FPS THỰC TẾ</span>
                      <span className="text-xl font-bold text-[#0E9384] font-mono mt-0.5 block">{data.benchmark.fps_achieved}</span>
                    </div>
                    <div className="p-3.5 rounded-lg bg-[#F8FAFC] border border-[#E4E9EF]">
                      <span className="text-xs text-[#667085] block">ĐỘ TRỄ TRUNG BÌNH</span>
                      <span className="text-xl font-bold text-[#175CD3] font-mono mt-0.5 block">{data.benchmark.overall_latency_ms} ms</span>
                    </div>
                    <div className="p-3.5 rounded-lg bg-[#F8FAFC] border border-[#E4E9EF]">
                      <span className="text-xs text-[#667085] block">ĐỘ TRỄ MIN / MAX</span>
                      <span className="text-sm font-semibold text-[#16202A] font-mono mt-1 block">
                        {data.benchmark.latency_min_ms} ms / {data.benchmark.latency_max_ms} ms
                      </span>
                    </div>
                    <div className="p-3.5 rounded-lg bg-[#F8FAFC] border border-[#E4E9EF]">
                      <span className="text-xs text-[#667085] block">PRECISION / RECALL</span>
                      <span className="text-sm font-semibold text-[#16202A] font-mono mt-1 block">
                        {data.benchmark.metrics?.precision ?? 'Chờ Ground Truth'}
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-10 text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-[#F8FAFC] border border-[#E4E9EF] flex items-center justify-center mx-auto text-[#98A2B3]">
                    <BarChart2 className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-[#16202A]">Chưa có dữ liệu đánh giá thực tế</h3>
                    <p className="text-sm text-[#475467] max-w-lg mx-auto mt-1">
                      Hệ thống không hiển thị số liệu ước lượng hoặc hard-code. Để có số liệu kiểm chuẩn định lượng thật, vui lòng chạy script benchmark trên video mẫu.
                    </p>
                  </div>
                  <div className="max-w-lg mx-auto p-3 rounded-lg bg-[#F8FAFC] font-mono text-xs text-[#344054] text-left border border-[#D0D7DE]">
                    <p className="text-[#667085] mb-1"># Chạy benchmark trên video kiểm thử đã khóa:</p>
                    <p className="text-[#175CD3]">python scripts/run_benchmark.py --video tests/benchmark/videos/dong_xe_may_hcm_01.mp4</p>
                  </div>
                </div>
              )}
            </TGCardContent>
          </TGCard>

          {/* 4. Kiến Trúc Quyết Định Trung Tâm */}
          <div className="p-5 rounded-xl bg-[#EFF4FF]/60 border border-[#B2CCFF] space-y-2">
            <h3 className="text-base font-bold text-[#175CD3] flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-[#175CD3]" />
              Nguyên Tắc Phân Xử Quyết Định (Decision Engine)
            </h3>
            <p className="text-sm text-[#344054] leading-relaxed">
              Mọi sự kiện từ camera đường bộ và camera cabin đều được đưa về <strong>Decision Engine</strong> trung tâm. Sự kiện đi qua bộ lọc chống nhiễu 3 tầng (Confidence Gating, Persistence qua N khung hình, Cooldown chống chớp tắt). Trọng tài ưu tiên áp dụng nguyên tắc: <strong>Va chạm khẩn cấp (TTC) &gt; Buồn ngủ (DMS) &gt; Cự ly an toàn &gt; Quá tốc độ &gt; Biển báo &gt; Thông tin</strong>. Cảnh báo mức độ nghiêm trọng có quyền ngắt (preempt) cảnh báo cấp thấp hơn và kích hoạt âm thanh cảnh báo tức thời.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
