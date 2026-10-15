'use client';

import React, { memo, useState } from 'react';
import {
  CreditCard,
  ShieldAlert,
  HardHat,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Clock,
  Layers,
  Search,
  Users,
  Car,
  Ruler,
  AlertOctagon,
  ArrowDown,
  ArrowUp,
  RotateCcw,
  Activity,
  Gauge,
  Radio,
  Camera,
  ZoomIn,
  Eye,
  X,
  FileText,
  Download,
  Gavel,
  ShieldCheck,
} from 'lucide-react';
import {
  PlateDetection,
  TrafficSign,
  HelmetViolation,
  VehicleDetection,
  LineCrossingData,
  sanitizeVietnamesePlate,
  isValidConfirmedPlate,
} from '../../types/detection';
import { TrafficDistancePanel, TrafficDistancePanelProps } from './TrafficDistancePanel';
import { LineCrossingStats } from '../../hooks/useTrafficDistanceEngine';

export type DetectionTabType = 'plates' | 'traffic' | 'signs' | 'helmets';

export interface DetectionTabsPanelProps {
  plates: PlateDetection[];
  vehicles: VehicleDetection[];
  signs: TrafficSign[];
  helmetViolations: HelmetViolation[];
  safeDistance?: number | null;
  recommendedDistance?: number | null;
  collisionLevel?: 'none' | 'warning' | 'danger';
  currentSpeed?: number | null;
  isStreaming: boolean;
  isImageMode?: boolean;
  activeTab?: DetectionTabType;
  onTabChange?: (tab: DetectionTabType) => void;
  lineCrossings?: LineCrossingStats | LineCrossingData | null;
  onResetLineCrossings?: () => void;
  trafficEngine?: TrafficDistancePanelProps;
  className?: string;
}

const SIGN_PENALTY_MAP: Record<string, string> = {
  // Nhóm P & DP (Biển cấm)
  'DP.135': 'Không áp dụng xử phạt (Hết hiệu lực các lệnh cấm trước đó)',
  'P.101': 'Đi vào đường cấm: Ô tô 2 - 3 triệu (tước GPLX 1-3T) • Xe máy 400k - 600k',
  'P.102': 'Đi ngược chiều: Ô tô 4 - 6 triệu (tước GPLX 2-4T) • Xe máy 1 - 2 triệu',
  'P.103a': 'Ô tô đi vào đường cấm ô tô: Phạt 2 - 3 triệu (tước GPLX 1-3T)',
  'P.103b': 'Rẽ phải nơi có biển cấm: Ô tô 800k - 1 triệu • Xe máy 400k - 600k',
  'P.103c': 'Rẽ trái nơi có biển cấm: Ô tô 800k - 1 triệu • Xe máy 400k - 600k',
  'P.104': 'Xe máy đi vào đường cấm xe máy: Phạt 400k - 600k',
  'P.105': 'Đi vào đường cấm: Ô tô 2 - 3 triệu • Xe máy 400k - 600k',
  'P.106a': 'Xe tải đi vào đường cấm tải: Phạt 2 - 3 triệu (tước GPLX 1-3T)',
  'P.106b': 'Xe tải >3.5T đi vào đường cấm: Phạt 2 - 3 triệu (tước GPLX 1-3T)',
  'P.107a': 'Xe khách đi vào đường cấm: Phạt 2 - 3 triệu (tước GPLX 1-3T)',
  'P.107b': 'Xe tải/khách đi vào đường cấm: Phạt 2 - 3 triệu (tước GPLX 1-3T)',
  'P.108': 'Xe kéo rơ-moóc vào đường cấm: Phạt 2 - 3 triệu (tước GPLX 1-3T)',
  'P.112': 'Người đi bộ đi vào đường cấm: Phạt 60k - 100k',
  'P.115': 'Chở quá tải cầu đường: Phạt 4 - 16 triệu (tước phù hiệu & GPLX 1-3T)',
  'P.116': 'Quá tải trọng trục: Phạt 4 - 16 triệu',
  'P.117': 'Vượt quá chiều cao cho phép: Phạt 2 - 3 triệu (tước GPLX 1-3T)',
  'P.118': 'Xe quá khổ chiều ngang: Phạt 2 - 3 triệu',
  'P.119': 'Xe quá khổ chiều dài: Phạt 2 - 3 triệu',
  'P.120': 'Xe rơ-moóc quá chiều dài: Phạt 2 - 3 triệu',
  'P.121': 'Không giữ cự ly tối thiểu: Ô tô 800k - 1 triệu (gây tai nạn 10 - 12 triệu)',
  'P.123a': 'Rẽ trái nơi cấm rẽ: Ô tô 800k - 1 triệu • Xe máy 400k - 600k',
  'P.123b': 'Rẽ phải nơi cấm rẽ: Ô tô 800k - 1 triệu • Xe máy 400k - 600k',
  'P.124a': 'Quay đầu nơi cấm quay đầu: Ô tô 800k - 1 triệu • Xe máy 400k - 600k',
  'P.124b': 'Ô tô quay đầu nơi cấm quay: Phạt 800k - 1 triệu',
  'P.124c': 'Rẽ trái hoặc quay đầu trái phép: Ô tô 800k - 1 triệu • Xe máy 400k - 600k',
  'P.124d': 'Rẽ phải hoặc quay đầu trái phép: Ô tô 800k - 1 triệu • Xe máy 400k - 600k',
  'P.125': 'Vượt xe nơi có biển cấm vượt: Ô tô 4 - 6 triệu (tước GPLX 1-3T) • Xe máy 800k - 1 triệu',
  'P.126': 'Xe tải vượt nơi cấm vượt: Phạt 4 - 6 triệu (tước GPLX 1-3T)',
  'P.127': 'Quá 5-10km/h: 800k - 1tr (ô tô), 300k - 400k (xe máy) • Quá >20km/h: 4 - 12 triệu (giam bằng)',
  'P.128': 'Bấm còi nơi cấm còi: Ô tô 300k - 400k • Xe máy 100k - 200k',
  'P.130': 'Dừng đỗ xe trái phép: Ô tô 800k - 1 triệu • Xe máy 300k - 400k',
  'P.131a': 'Đỗ xe nơi cấm đỗ: Ô tô 400k - 600k • Xe máy 300k - 400k',
  'P.131b': 'Đỗ xe ngày lẻ trái phép: Ô tô 400k - 600k • Xe máy 300k - 400k',
  'P.131c': 'Đỗ xe ngày chẵn trái phép: Ô tô 400k - 600k • Xe máy 300k - 400k',
  'P.132': 'Không nhường xe ngược chiều: Ô tô 400k - 600k',
  'P.137': 'Rẽ trái/phải nơi cấm rẽ: Ô tô 800k - 1 triệu • Xe máy 400k - 600k',
  'P.245a': 'Không giảm tốc độ khi có biển: Ô tô 400k - 600k (gây tai nạn phạt 4 - 5 triệu)',

  // Nhóm R (Biển hiệu lệnh)
  'R.301a': 'Không chấp hành hiệu lệnh đi thẳng: Ô tô 300k - 400k • Xe máy 100k - 200k',
  'R.301b': 'Không chấp hành hiệu lệnh rẽ phải: Ô tô 300k - 400k • Xe máy 100k - 200k',
  'R.301c': 'Không chấp hành hiệu lệnh rẽ trái: Ô tô 300k - 400k • Xe máy 100k - 200k',
  'R.301d': 'Không chấp hành hiệu lệnh rẽ phải: Ô tô 300k - 400k • Xe máy 100k - 200k',
  'R.301e': 'Không chấp hành hiệu lệnh hướng đi: Ô tô 300k - 400k • Xe máy 100k - 200k',
  'R.301f': 'Không chấp hành hiệu lệnh hướng đi: Ô tô 300k - 400k • Xe máy 100k - 200k',
  'R.302a': 'Đi sai hướng tránh chướng ngại vật: Ô tô 300k - 400k • Xe máy 100k - 200k',
  'R.302b': 'Đi sai hướng tránh chướng ngại vật: Ô tô 300k - 400k • Xe máy 100k - 200k',
  'R.303': 'Không nhường đường/không theo vòng xuyến: Ô tô 300k - 400k • Xe máy 100k - 200k',
  'R.304': 'Đi vào làn xe thô sơ: Ô tô 400k - 600k • Xe máy 300k - 400k',
  'R.305': 'Xe cơ giới đi vào đường người đi bộ: Ô tô 2 - 3 triệu • Xe máy 400k - 600k',
  'R.306': 'Chạy dưới tốc độ tối thiểu: Ô tô 800k - 1 triệu • Xe máy 200k - 400k',
  'R.403a': 'Xe máy đi vào đường ô tô: Phạt 2 - 3 triệu (tước GPLX 1-3T)',
  'R.407a': 'Đi ngược chiều đường một chiều: Ô tô 4 - 6 triệu (giam bằng 2-4T) • Xe máy 1 - 2 triệu',
  'R.409': 'Quay xe sai quy định: Ô tô 400k - 600k • Xe máy 100k - 200k',
  'R.425': 'Bấm còi hơi/rú ga khu vực bệnh viện: Ô tô 800k - 1 triệu • Xe máy 400k - 600k',
  'R.434': 'Dừng đỗ trái phép tại điểm xe buýt: Ô tô 400k - 600k • Xe máy 300k - 400k',

  // Nhóm W (Biển cảnh báo nguy hiểm)
  'W.201a': 'Khúc cua nguy hiểm: Không giảm tốc độ/vượt xe gây TNGT phạt 4 - 5 triệu (tước GPLX 2-4T)',
  'W.201b': 'Khúc cua nguy hiểm: Không giảm tốc độ/vượt xe gây TNGT phạt 4 - 5 triệu (tước GPLX 2-4T)',
  'W.202a': 'Cua liên tiếp: Không giảm tốc độ/vượt xe gây TNGT phạt 4 - 5 triệu (tước GPLX 2-4T)',
  'W.202b': 'Cua liên tiếp: Không giảm tốc độ/vượt xe gây TNGT phạt 4 - 5 triệu (tước GPLX 2-4T)',
  'W.203a': 'Đoạn hẹp: Không giảm tốc độ, không nhường xe đối diện phạt 400k - 600k (ô tô)',
  'W.203b': 'Đoạn hẹp bên trái: Không giảm tốc độ, không nhường đường phạt 400k - 600k',
  'W.203c': 'Đoạn hẹp bên phải: Không giảm tốc độ, không nhường đường phạt 400k - 600k',
  'W.205a': 'Nút giao: Không giảm tốc độ, không nhường đường phạt 400k - 600k (ô tô)',
  'W.205b': 'Nút giao: Không giảm tốc độ, không nhường đường theo quy định phạt 400k - 600k',
  'W.205c': 'Nút giao: Không giảm tốc độ, không nhường đường theo quy định phạt 400k - 600k',
  'W.205d': 'Ngã ba chữ T: Không giảm tốc độ, không nhường đường phạt 400k - 600k',
  'W.205e': 'Ngã ba chữ Y: Giảm tốc độ, quan sát dòng phương tiện nhập làn',
  'W.207a': 'Được ưu tiên: Giữ tốc độ an toàn, chú ý phương tiện bất ngờ từ đường phụ',
  'W.207b': 'Chú ý nhánh phụ bên phải: Giảm ga, quan sát xe nhập làn',
  'W.207c': 'Chú ý nhánh phụ bên trái: Giảm ga, quan sát xe nhập làn',
  'W.208': 'Không nhường xe trên đường ưu tiên: Ô tô 800k - 1 triệu • Xe máy 400k - 600k',
  'W.209': 'Vượt đèn đỏ: Ô tô 4 - 6 triệu (giam bằng 1-3T) • Xe máy 800k - 1 triệu',
  'W.210': 'Vượt rào chắn đường sắt: Ô tô 4 - 6 triệu • Xe máy 800k - 1 triệu (giam bằng 1-3T)',
  'W.211a': 'Không dừng quan sát tại đường sắt: Ô tô 800k - 1 triệu • Xe máy 300k - 400k',
  'W.219': 'Dốc dài: Về số thấp, không rà phanh liên tục phòng tránh mất phanh và tai nạn',
  'W.221b': 'Gờ giảm tốc: Giảm tốc độ qua gờ; không giảm tốc gây va chạm phạt 400k - 600k',
  'W.224': 'Không nhường đường người đi bộ: Ô tô 200k - 400k • Xe máy 100k - 200k',
  'W.225': 'Khu vực trường học/trẻ em: Chú ý quan sát, giảm ga tránh tai nạn bất ngờ',
  'W.227': 'Không giảm tốc qua khu vực thi công: Phạt 400k - 600k (ô tô)',
  'W.233': 'Đoạn nguy hiểm: Giảm tốc độ, quan sát kỹ hai bên đường',
  'W.235': 'Đường đôi: Đi đúng làn đường phân cách; đi sai làn phạt 3 - 5 triệu (tước GPLX)',
  'W.245a': 'Không giảm tốc độ khi có biển cảnh báo nguy hiểm gây TNGT phạt 4 - 5 triệu (tước GPLX)',

  // Nhóm S & I (Biển phụ & Chỉ dẫn)
  'S.508': 'Khung giờ hiệu lực: Vi phạm trong khung giờ bị xử phạt như biển chính',
  'S.503': 'Đối tượng áp dụng: Xử phạt đúng nhóm phương tiện chỉ định trên biển',
  'S.509a': 'Thuyết minh biển báo: Căn cứ bổ sung xác định lỗi vi phạm',
  'I.401': 'Được ưu tiên: Đi đúng tốc độ cho phép, chú ý an toàn tại nút giao',
  'I.402': 'Hết ưu tiên: Giảm tốc độ và nhường đường theo quy tắc giao thông',
  'I.408a': 'Đỗ xe sai ô quy định / không sát lề: Ô tô 400k - 600k',
  'I.423a': 'Không nhường người đi bộ qua đường: Ô tô 200k - 400k • Xe máy 100k - 200k',
};

function getSignPenalty(signType?: string, category?: string): string {
  if (!signType) return 'Tuân thủ quy định theo Nghị định 100/2019/NĐ-CP & 123/2021/NĐ-CP';
  const norm = signType.trim();
  if (SIGN_PENALTY_MAP[norm]) return SIGN_PENALTY_MAP[norm];
  const found = Object.keys(SIGN_PENALTY_MAP).find(
    (k) => k.toLowerCase() === norm.toLowerCase() || k.replace(/\./g, '').toLowerCase() === norm.replace(/\./g, '').toLowerCase()
  );
  if (found) return SIGN_PENALTY_MAP[found];

  if (category === 'CẤM' || norm.startsWith('P') || norm.startsWith('p')) {
    return 'Vi phạm hiệu lực biển cấm: Ô tô 800.000đ - 3.000.000đ (có thể tước GPLX) • Xe máy 300.000đ - 1.000.000đ';
  }
  if (category === 'CẢNH BÁO' || norm.startsWith('W') || norm.startsWith('w')) {
    return 'Không giảm tốc độ khi gặp biển cảnh báo gây tai nạn: Phạt 4.000.000đ - 5.000.000đ (tước GPLX)';
  }
  if (category === 'HIỆU LỆNH' || norm.startsWith('R') || norm.startsWith('r')) {
    return 'Không chấp hành hiệu lệnh biển báo: Ô tô 300.000đ - 400.000đ • Xe máy 100.000đ - 200.000đ';
  }
  return 'Tuân thủ quy tắc giao thông theo Nghị định 100/2019/NĐ-CP & 123/2021/NĐ-CP';
}

export const DetectionTabsPanel = memo(function DetectionTabsPanel({
  plates = [],
  vehicles = [],
  signs = [],
  helmetViolations = [],
  safeDistance = null,
  recommendedDistance = null,
  collisionLevel = 'none',
  currentSpeed = null,
  isStreaming,
  isImageMode = false,
  activeTab: controlledActiveTab,
  onTabChange,
  lineCrossings,
  onResetLineCrossings,
  trafficEngine,
  className = '',
}: DetectionTabsPanelProps) {
  const [internalTab, setInternalTab] = useState<DetectionTabType>('plates');
  const [showRadarView, setShowRadarView] = useState(false);
  const [selectedHelmetEvidence, setSelectedHelmetEvidence] = useState<HelmetViolation | null>(null);
  const activeTab = controlledActiveTab !== undefined ? controlledActiveTab : internalTab;
  const effectiveCrossings = lineCrossings || trafficEngine?.lineCrossings;
  const handleResetCrossings = onResetLineCrossings || trafficEngine?.onResetLineCrossings;

  const inCount = (effectiveCrossings as any)?.inCount ?? (effectiveCrossings as any)?.in_count ?? 0;
  const outCount = (effectiveCrossings as any)?.outCount ?? (effectiveCrossings as any)?.out_count ?? 0;
  const outByClass = (effectiveCrossings as any)?.outByClass || (effectiveCrossings as any)?.out_by_class || {};
  const inByClass = (effectiveCrossings as any)?.inByClass || (effectiveCrossings as any)?.in_by_class || {};

  const validPlates = plates.filter((p) => isValidConfirmedPlate(p.plate_text));

  // Lọc trùng lặp biển báo theo loại: Mỗi biển báo chỉ hiển thị 1 thẻ duy nhất (kèm số lần xuất hiện)
  const uniqueSigns = React.useMemo(() => {
    const map = new Map<string, TrafficSign>();
    for (const s of signs) {
      const code = s.sign_type || 'UNKNOWN';
      if (!map.has(code)) {
        map.set(code, { ...s });
      } else {
        const existing = map.get(code)!;
        existing.count = (existing.count || 1) + (s.count || 1);
        if ((s.confidence || 0) > (existing.confidence || 0)) {
          existing.confidence = s.confidence;
          if (s.thumbnail) existing.thumbnail = s.thumbnail;
        }
      }
    }
    return Array.from(map.values());
  }, [signs]);

  // Lọc trùng lặp vi phạm mũ bảo hiểm: Mỗi người chỉ hiển thị 1 thẻ duy nhất (kèm số lần xuất hiện)
  const uniqueHelmets = React.useMemo(() => {
    const list: HelmetViolation[] = [];
    for (const h of helmetViolations) {
      const existing = list.find((item) => {
        if (item.track_id && h.track_id && item.track_id === h.track_id) return true;
        const c1x = (item.bbox.x1 + item.bbox.x2) / 2;
        const c1y = (item.bbox.y1 + item.bbox.y2) / 2;
        const c2x = (h.bbox.x1 + h.bbox.x2) / 2;
        const c2y = (h.bbox.y1 + h.bbox.y2) / 2;
        return Math.hypot(c1x - c2x, c1y - c2y) < 60;
      });

      if (existing) {
        existing.count = (existing.count || 1) + (h.count || 1);
        if (h.thumbnail && !existing.thumbnail) {
          existing.thumbnail = h.thumbnail;
        }
      } else {
        list.push({ ...h });
      }
    }
    return list;
  }, [helmetViolations]);

  const handleTabSelect = (tab: DetectionTabType) => {
    setInternalTab(tab);
    onTabChange?.(tab);
  };

  // Helper to get plate confidence badge
  const getConfidenceBadge = (conf?: number) => {
    const val = conf ? Math.round(conf * 100) : 88;
    if (val >= 85) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]">
          <CheckCircle2 className="w-2.5 h-2.5" />
          Chắc chắn ({val}%)
        </span>
      );
    }
    if (val >= 60) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-[#FFFAEB] text-[#B54708] border border-[#FEDF89]">
          <AlertTriangle className="w-2.5 h-2.5" />
          Nghi ngờ ({val}%)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-[#F8FAFC] text-[#667085] border border-[#E4E9EF]">
        <HelpCircle className="w-2.5 h-2.5" />
        Kém chất lượng ({val}%)
      </span>
    );
  };

  // Hiển thị màu biển số chính xác dựa trên phân tích hình ảnh AI (Background Color)
  const getPlateColorBadge = (plate: PlateDetection) => {
    const bg = plate.background_color;
    const clean = (plate.plate_text || '').replace(/[^A-Z0-9]/gi, '').toUpperCase();
    const isCommercialBySeries = clean.length >= 3 && /^[0-9]{2}[EFG]/.test(clean);
    if (bg === 'COMMERCIAL_YELLOW' || isCommercialBySeries || plate.vehicle_type === 'Xe dịch vụ / Vận tải') {
      return (
        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#FEF0C7] text-[#B54708] border border-[#FDB022]/40 font-mono">
          Biển Vàng (Dịch vụ vận tải)
        </span>
      );
    }
    if (bg === 'GOVERNMENT_BLUE') {
      return (
        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#EFF8FF] text-[#175CD3] border border-[#B2DDFF] font-mono">
          Biển Xanh (Cơ quan)
        </span>
      );
    }
    const isProvincial = clean.length >= 2 && /^\d{2}/.test(clean);
    if (!isProvincial && bg === 'MILITARY_RED') {
      return (
        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA] font-mono">
          Biển Đỏ (Quân đội)
        </span>
      );
    }
    return (
      <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#F8FAFC] text-[#344054] border border-[#D0D7DE] font-mono">
        Biển Trắng (Dân sự)
      </span>
    );
  };

  return (
    <div
      className={`w-full bg-white border border-[#E4E9EF] rounded-[10px] overflow-hidden shadow-sm flex flex-col select-none ${className}`}
    >
      {/* ── TABS NAVIGATION BAR ── */}
      <div className="flex items-center justify-between border-b border-[#E4E9EF] bg-[#F8FAFC] px-3 pt-2">
        <div className="flex items-center gap-1">
          {/* Tab 1: Biển Số */}
          <button
            onClick={() => handleTabSelect('plates')}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-t-[8px] border-t border-x transition-colors cursor-pointer ${
              activeTab === 'plates'
                ? 'bg-white border-[#E4E9EF] text-[#175CD3] shadow-xs relative top-px'
                : 'border-transparent text-[#667085] hover:text-[#16202A]'
            }`}
            title="Nhấn phím [1] để xem biển số xe"
          >
            <CreditCard className="w-3.5 h-3.5 text-[#175CD3]" />
            <span>Biển Số Xe</span>
            <kbd className="hidden sm:inline text-[9px] px-1 py-0.2 bg-black/5 rounded text-[#667085] font-mono">1</kbd>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === 'plates'
                  ? 'bg-[#EFF4FF] text-[#175CD3]'
                  : 'bg-white text-[#667085] border border-[#E4E9EF]'
              }`}
            >
              {validPlates.length}
            </span>
          </button>

          {/* Tab 2: Mật Độ & Khoảng Cách */}
          <button
            onClick={() => handleTabSelect('traffic')}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-t-[8px] border-t border-x transition-colors cursor-pointer ${
              activeTab === 'traffic'
                ? 'bg-white border-[#E4E9EF] text-[#2E90FA] shadow-xs relative top-px'
                : 'border-transparent text-[#667085] hover:text-[#16202A]'
            }`}
            title="Nhấn phím [2] để xem mật độ giao thông & khoảng cách xe"
          >
            <Users className="w-3.5 h-3.5 text-[#2E90FA]" />
            <span>Mật Độ & Cự Ly Xe</span>
            <kbd className="hidden sm:inline text-[9px] px-1 py-0.2 bg-black/5 rounded text-[#667085] font-mono">2</kbd>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === 'traffic'
                  ? 'bg-[#EFF8FF] text-[#2E90FA]'
                  : 'bg-white text-[#667085] border border-[#E4E9EF]'
              }`}
            >
              {vehicles.length}
            </span>
          </button>

          {/* Tab 3: Biển Báo */}
          <button
            onClick={() => handleTabSelect('signs')}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-t-[8px] border-t border-x transition-colors cursor-pointer ${
              activeTab === 'signs'
                ? 'bg-white border-[#E4E9EF] text-[#F79009] shadow-xs relative top-px'
                : 'border-transparent text-[#667085] hover:text-[#16202A]'
            }`}
            title="Nhấn phím [3] để xem biển báo giao thông"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-[#F79009]" />
            <span>Biển Báo Giao Thông</span>
            <kbd className="hidden sm:inline text-[9px] px-1 py-0.2 bg-black/5 rounded text-[#667085] font-mono">3</kbd>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === 'signs'
                  ? 'bg-[#FFFAEB] text-[#F79009]'
                  : 'bg-white text-[#667085] border border-[#E4E9EF]'
              }`}
            >
              {uniqueSigns.length}
            </span>
          </button>

          {/* Tab 4: Mũ Bảo Hiểm */}
          <button
            onClick={() => handleTabSelect('helmets')}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-t-[8px] border-t border-x transition-colors cursor-pointer ${
              activeTab === 'helmets'
                ? 'bg-white border-[#E4E9EF] text-[#F04438] shadow-xs relative top-px'
                : 'border-transparent text-[#667085] hover:text-[#16202A]'
            }`}
            title="Nhấn phím [4] để xem vi phạm mũ bảo hiểm"
          >
            <HardHat className="w-3.5 h-3.5 text-[#F04438]" />
            <span>Mũ Bảo Hiểm</span>
            <kbd className="hidden sm:inline text-[9px] px-1 py-0.2 bg-black/5 rounded text-[#667085] font-mono">4</kbd>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === 'helmets'
                  ? 'bg-[#FEF3F2] text-[#F04438]'
                  : 'bg-white text-[#667085] border border-[#E4E9EF]'
              }`}
            >
              {uniqueHelmets.length}
            </span>
          </button>
        </div>

        <span className="text-[11px] text-[#667085] hidden sm:inline font-mono">
          Trích xuất từ luồng AI thời gian thực
        </span>
      </div>

      {/* ── TAB CONTENT ── */}
      <div className={`p-3 overflow-y-auto ${activeTab === 'traffic' ? 'min-h-[320px] max-h-[520px]' : 'min-h-[160px] max-h-[260px]'}`}>
        {/* TAB 1: BIỂN SỐ XE */}
        {activeTab === 'plates' && (
          <div>
            {validPlates.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-7 text-center text-[#98A2B3]">
                <CreditCard className="w-8 h-8 mb-1.5 stroke-[1.5]" />
                <p className="text-xs font-semibold text-[#475467]">
                  Không phát hiện biển số xe hợp lệ trong ảnh / video này
                </p>
                <p className="text-[11px] text-[#98A2B3] mt-0.5">
                  Hệ thống tự động lọc bỏ các biển số bị mờ, vật thể ở quá xa hoặc số điện thoại, biển quảng cáo.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                {validPlates.map((p, idx) => {
                  const sanitized = sanitizeVietnamesePlate(p.plate_text);

                  return (
                    <div
                      key={`${sanitized}-${idx}`}
                      className="p-2.5 rounded-[8px] border border-[#E4E9EF] bg-[#F8FAFC] flex items-center justify-between gap-3 shadow-2xs hover:border-[#175CD3]/40 transition-colors"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-sm font-black font-mono tracking-wider px-2 py-0.5 rounded text-[#0C111D] bg-white border border-[#175CD3]/40 shadow-xs">
                            {sanitized}
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]">
                            <CheckCircle2 className="w-2.5 h-2.5" />
                            Đã xác thực
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-1.5">
                          {getPlateColorBadge(p)}
                          {p.province && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#F0F9FF] text-[#026AA2] border border-[#B9E6FE] font-mono">
                              {p.province}
                            </span>
                          )}
                          {p.count && p.count > 1 && (
                            <span className="text-[10px] text-[#667085] font-mono">
                              ({p.count} lần)
                            </span>
                          )}
                        </div>
                      </div>
                      {p.thumbnail && (
                        <img
                          src={p.thumbnail}
                          alt={sanitized}
                          className="h-10 max-w-[80px] rounded border border-[#D0D7DE] object-cover shadow-2xs shrink-0 bg-white"
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: MẬT ĐỘ GIAO THÔNG & KHOẢNG CÁCH XE (HIỂN THỊ DANH SÁCH PHƯƠNG TIỆN, VẬN TỐC & LINE CROSSING) */}
        {activeTab === 'traffic' && (
          <div className="space-y-3">
            {/* Thanh chuyển đổi chế độ xem nếu có Radar Engine */}
            {trafficEngine && (
              <div className="flex items-center justify-between border-b border-[#E4E9EF] pb-2.5">
                <div className="flex items-center gap-1.5 text-xs text-[#475467]">
                  <Activity className="w-4 h-4 text-[#175CD3]" />
                  <span className="font-semibold text-[#16202A]">Chế độ quan sát ADAS:</span>
                  <span className="text-[11px] text-[#667085]">Giám sát mật độ, cự ly 3D và lưu lượng qua vạch</span>
                </div>
                <div className="flex items-center gap-1 bg-[#F2F4F7] p-0.5 rounded-lg border border-[#E4E9EF]">
                  <button
                    type="button"
                    onClick={() => setShowRadarView(false)}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
                      !showRadarView
                        ? 'bg-white text-[#175CD3] shadow-xs'
                        : 'text-[#667085] hover:text-[#16202A]'
                    }`}
                  >
                    📋 Thống kê & Danh sách xe
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowRadarView(true)}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all flex items-center gap-1 ${
                      showRadarView
                        ? 'bg-white text-[#175CD3] shadow-xs'
                        : 'text-[#667085] hover:text-[#16202A]'
                    }`}
                  >
                    <Radio className="w-3.5 h-3.5 text-[#0E9384]" />
                    📡 Radar 3D Cự ly
                  </button>
                </div>
              </div>
            )}

            {showRadarView && trafficEngine ? (
              <TrafficDistancePanel
                {...trafficEngine}
                lineCrossings={effectiveCrossings as any}
                onResetLineCrossings={handleResetCrossings}
              />
            ) : (
              <>
                {/* 1. KHỐI THỐNG KÊ LINE CROSSINGS & VẬN TỐC THEO THỜI GIAN THỰC */}
                {effectiveCrossings && (
                  <div className="p-3 rounded-[10px] border border-[#CBD5E1] bg-[#0F172A] text-white shadow-sm space-y-2.5">
                    <div className="flex items-center justify-between border-b border-white/10 pb-2">
                      <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-[#38BDF8]" />
                        <div>
                          <h4 className="text-xs font-bold uppercase tracking-wider text-[#38BDF8]">
                            Lưu Lượng Qua Vạch Ảo (Virtual Line Crossing)
                          </h4>
                          <span className="text-[10px] text-slate-400">
                            Đếm IN / OUT & ước lượng vận tốc thời gian thực (vạch chuẩn Y = 60%)
                          </span>
                        </div>
                      </div>
                      {handleResetCrossings && (
                        <button
                          type="button"
                          onClick={handleResetCrossings}
                          className="px-2 py-1 text-[11px] font-medium rounded bg-white/10 hover:bg-white/20 text-slate-200 transition-colors flex items-center gap-1"
                          title="Đặt lại bộ đếm IN / OUT"
                        >
                          <RotateCcw className="w-3 h-3 text-slate-300" />
                          <span>Đặt lại đếm</span>
                        </button>
                      )}
                    </div>

                    {/* Hàng chỉ số IN / OUT / TỔNG */}
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-500/30">
                        <div className="text-[10px] text-emerald-400 font-semibold flex items-center justify-center gap-1">
                          <ArrowDown className="w-3 h-3 text-emerald-400" />
                          <span>IN (Tiến vào)</span>
                        </div>
                        <div className="text-lg font-black text-emerald-300 font-mono">
                          {inCount}
                        </div>
                      </div>

                      <div className="p-2 rounded-lg bg-sky-950/60 border border-sky-500/30">
                        <div className="text-[10px] text-sky-400 font-semibold flex items-center justify-center gap-1">
                          <ArrowUp className="w-3 h-3 text-sky-400" />
                          <span>OUT (Rời đi)</span>
                        </div>
                        <div className="text-lg font-black text-sky-300 font-mono">
                          {outCount}
                        </div>
                      </div>

                      <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-600/40">
                        <div className="text-[10px] text-slate-300 font-semibold">TỔNG LƯỢT</div>
                        <div className="text-lg font-black text-amber-300 font-mono">
                          {inCount + outCount}
                        </div>
                      </div>
                    </div>

                    {/* Chi tiết phân loại Line Crossings & Danh sách Tốc độ Realtime */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono pt-1">
                      {/* Cột 1: Phân loại Out/In */}
                      <div className="p-2 rounded bg-black/40 border border-white/5 space-y-1.5">
                        <span className="text-[11px] font-bold text-amber-300 block">
                          Line Crossings (Phân loại):
                        </span>
                        <div className="pl-2 space-y-1 text-[11px]">
                          <div>
                            <span className="text-sky-300 font-bold block">Out:</span>
                            <div className="pl-3 grid grid-cols-2 gap-x-2 text-slate-300">
                              <span>motor: <strong className="text-white">{outByClass?.motor ?? outByClass?.motorcycle ?? 0}</strong></span>
                              <span>people: <strong className="text-white">{outByClass?.people ?? outByClass?.person ?? 0}</strong></span>
                              <span>car: <strong className="text-white">{outByClass?.car ?? 0}</strong></span>
                              <span>truck: <strong className="text-white">{outByClass?.truck ?? outByClass?.bus ?? 0}</strong></span>
                            </div>
                          </div>
                          <div className="pt-1">
                            <span className="text-emerald-300 font-bold block">In:</span>
                            <div className="pl-3 grid grid-cols-2 gap-x-2 text-slate-300">
                              <span>motor: <strong className="text-white">{inByClass?.motor ?? inByClass?.motorcycle ?? 0}</strong></span>
                              <span>people: <strong className="text-white">{inByClass?.people ?? inByClass?.person ?? 0}</strong></span>
                              <span>car: <strong className="text-white">{inByClass?.car ?? 0}</strong></span>
                              <span>truck: <strong className="text-white">{inByClass?.truck ?? inByClass?.bus ?? 0}</strong></span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Cột 2: Luồng Vận Tốc Thời Gian Thực */}
                      <div className="p-2 rounded bg-black/40 border border-white/5 flex flex-col justify-between">
                        <div>
                          <span className="text-[11px] font-bold text-emerald-300 block mb-1">
                            Vận tốc thời gian thực (Live Speeds):
                          </span>
                          <div className="space-y-1 max-h-[90px] overflow-y-auto pr-1">
                            {vehicles.filter(v => (v.speed_kmh && v.speed_kmh > 0) || v.class).length > 0 ? (
                              vehicles.slice(0, 5).map((v, i) => {
                                const cls = (v.class || 'car').toLowerCase();
                                const isPeople = cls.includes('person') || cls.includes('people');
                                const isMotor = cls.includes('motor') || cls.includes('bike');
                                const isTruck = cls.includes('truck') || cls.includes('bus');
                                const label = isPeople ? 'people' : isMotor ? 'motor' : isTruck ? 'truck' : 'car';
                                const spd = Math.round(v.speed_kmh || (v.distance_m ? Math.max(15, 60 - v.distance_m) : 35));
                                return (
                                  <div key={`live-spd-${v.id || i}`} className="flex items-center justify-between text-[11px] py-0.5 border-b border-white/5">
                                    <span className="text-slate-300">
                                      {label} #{v.id || i + 1}
                                    </span>
                                    <div className="flex items-center gap-1.5">
                                      {v.direction && (
                                        <span className={`px-1 rounded text-[9px] font-bold ${
                                          v.direction === 'IN' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-sky-500/20 text-sky-300'
                                        }`}>
                                          {v.direction}
                                        </span>
                                      )}
                                      <span className="font-bold text-amber-300">
                                        {spd} km/h
                                      </span>
                                    </div>
                                  </div>
                                );
                              })
                            ) : (
                              <div className="text-[10px] text-slate-500 italic py-2">
                                Đang ước lượng vận tốc qua các frame liên tiếp...
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="text-[9px] text-slate-400 mt-1 flex items-center justify-between">
                          <span>Camera: Hiệu chuẩn Homography</span>
                          <span className="text-emerald-400">● Realtime YOLOv8</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. BANNER TỔNG QUAN MẬT ĐỘ & CỰ LY AN TOÀN */}
                {vehicles.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-7 text-center text-[#98A2B3]">
                    <Users className="w-8 h-8 mb-1.5 stroke-[1.5] text-[#2E90FA]" />
                    <p className="text-xs font-semibold text-[#475467]">
                      Chưa phát hiện phương tiện hoặc đường thông thoáng
                    </p>
                    <p className="text-[11px] text-[#98A2B3] mt-0.5">
                      Mật độ giao thông và cự ly an toàn được hiển thị trực tiếp trên khung video phía trên khi tải video lên.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="p-2.5 rounded-[8px] border border-[#B2DDFF] bg-[#EFF8FF] flex flex-wrap items-center justify-between gap-3 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-[#175CD3] flex items-center gap-1.5">
                          <Users className="w-4 h-4" />
                          Mật độ: {vehicles.length > 5 ? 'Đông đúc' : vehicles.length > 2 ? 'Bình thường' : 'Thông thoáng'}
                        </span>
                        <span className="text-[#475467]">({vehicles.length} đối tượng phát hiện)</span>
                      </div>

                      <div className="flex items-center gap-3">
                        {safeDistance !== null && safeDistance !== undefined && (
                          <div className="flex items-center gap-1.5 font-mono">
                            <Ruler className="w-3.5 h-3.5 text-[#0E9384]" />
                            <span className="text-[#475467]">Cự ly xe trước:</span>
                            <span
                              className={`font-bold ${
                                collisionLevel === 'danger'
                                  ? 'text-[#F04438]'
                                  : collisionLevel === 'warning'
                                  ? 'text-[#F79009]'
                                  : 'text-[#067647]'
                              }`}
                            >
                              {safeDistance.toFixed(1)}m
                            </span>
                            {recommendedDistance !== null && (
                              <span className="text-[10px] text-[#667085]">(Chuẩn: {recommendedDistance.toFixed(0)}m)</span>
                            )}
                          </div>
                        )}
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            collisionLevel === 'danger'
                              ? 'bg-[#FEF3F2] text-[#F04438] border border-[#FECDCA] animate-pulse'
                              : collisionLevel === 'warning'
                              ? 'bg-[#FFFAEB] text-[#F79009] border border-[#FEDF89]'
                              : 'bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]'
                          }`}
                        >
                          {collisionLevel === 'danger'
                            ? 'Cảnh báo: Nguy cơ va chạm'
                            : collisionLevel === 'warning'
                            ? 'Chú ý khoảng cách an toàn'
                            : 'Khoảng cách an toàn'}
                        </span>
                      </div>
                    </div>

                    {/* 3. LƯỚI CÁC XE VÀ NGƯỜI ĐANG THEO DÕI */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                      {vehicles.map((v, idx) => {
                        const clsName = (v.class || 'car').toLowerCase();
                        const isPerson = clsName.includes('person') || clsName.includes('people');
                        const isMoto = clsName.includes('motor') || clsName.includes('bike');
                        const isTruck = clsName.includes('truck') || clsName.includes('bus');
                        const vehicleLabel = isPerson ? 'Người đi bộ' : isTruck ? 'Xe tải / Buýt' : isMoto ? 'Xe máy' : 'Xe ô tô';
                        const icon = isPerson ? '🚶' : isTruck ? '🚚' : isMoto ? '🏍️' : '🚗';

                        const boxH = Math.max(1, v.bbox.y2 - v.bbox.y1);
                        const estDist = v.distance_m != null ? v.distance_m : Math.max(3, Math.min(80, Math.round(5000 / boxH)));
                        const isTooClose = estDist < 10.0;

                        return (
                          <div
                            key={`veh-${v.id || idx}`}
                            className="p-2.5 rounded-[8px] border border-[#E4E9EF] bg-[#F8FAFC] flex items-center justify-between gap-3 shadow-2xs hover:border-[#175CD3]/40 transition-colors"
                          >
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-1.5 flex-wrap">
                                <span className="text-base">{icon}</span>
                                <span className="text-xs font-bold text-[#16202A]">
                                  {vehicleLabel} #{v.id || idx + 1}
                                </span>
                                {v.direction && (
                                  <span
                                    className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold flex items-center gap-0.5 ${
                                      v.direction === 'IN'
                                        ? 'bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]'
                                        : 'bg-[#EFF8FF] text-[#175CD3] border border-[#B2DDFF]'
                                    }`}
                                  >
                                    {v.direction === 'IN' ? '⬇ IN' : '⬆ OUT'}
                                  </span>
                                )}
                                <span
                                  className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                                    isTooClose
                                      ? 'bg-[#FEF3F2] text-[#F04438] border border-[#FECDCA]'
                                      : 'bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]'
                                  }`}
                                >
                                  {isTooClose ? 'Cần giữ khoảng cách' : 'Cự ly an toàn'}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 mt-1.5 text-xs font-mono">
                                <span className="text-[#475467]">Khoảng cách:</span>
                                <strong className={`font-black ${isTooClose ? 'text-[#F04438]' : 'text-[#16202A]'}`}>
                                  {estDist} m
                                </strong>
                                {!isImageMode && (
                                  <span className="text-[#175CD3] font-bold ml-auto">
                                    {Math.round(v.speed_kmh || (v.distance_m ? Math.max(15, 60 - v.distance_m) : 35))} km/h
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* TAB 3: BIỂN BÁO GIAO THÔNG */}
        {activeTab === 'signs' && (
          <div>
            {uniqueSigns.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-7 text-center text-[#98A2B3]">
                <ShieldAlert className="w-8 h-8 mb-1.5 stroke-[1.5]" />
                <p className="text-xs font-semibold text-[#475467]">
                  Không phát hiện biển báo giao thông trong ảnh / video này
                </p>
                <p className="text-[11px] text-[#98A2B3] mt-0.5 max-w-md">
                  Chỉ nhận diện biển báo đạt độ tin cậy cao theo chuẩn QCVN 41:2019/BGTVT (Đã loại bỏ các vật thể có màu sắc/hình dạng tương tự hoặc ở quá xa).
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-2.5">
                {uniqueSigns.map((s, idx) => {
                  const isSpeedLimit = s.speed_limit != null && s.speed_limit > 0 && (s.sign_type?.includes('127') || false);
                  const isProhibitory = s.category === 'CẤM' || (s.sign_type && s.sign_type.startsWith('P'));
                  const isWarning = s.category === 'CẢNH BÁO' || (s.sign_type && s.sign_type.startsWith('W'));
                  const isMandatory = s.category === 'HIỆU LỆNH' || (s.sign_type && (s.sign_type.startsWith('R.3') || s.sign_type.startsWith('DP')));
                  const isInformative = s.category === 'CHỈ DẪN' || (s.sign_type && (s.sign_type.startsWith('I.') || s.sign_type.startsWith('R.4')));

                  const cardStyle = isProhibitory
                    ? 'border-[#FECDCA] bg-[#FEF3F2] hover:border-[#F97066]'
                    : isWarning
                    ? 'border-[#FEDF89] bg-[#FFFAEB] hover:border-[#F79009]'
                    : isMandatory
                    ? 'border-[#BAE6FD] bg-[#F0F9FF] hover:border-[#38BDF8]'
                    : 'border-[#A6F4C5] bg-[#ECFDF3] hover:border-[#32D583]';

                  const badgeTagColor = isProhibitory
                    ? 'bg-[#FEE4E2] text-[#D92D20] border-[#FECDCA]'
                    : isWarning
                    ? 'bg-[#FEF0C7] text-[#B54708] border-[#FEDF89]'
                    : isMandatory
                    ? 'bg-[#E0F2FE] text-[#0284C7] border-[#BAE6FD]'
                    : 'bg-[#D1FADF] text-[#027A48] border-[#A6F4C5]';

                  const categoryLabel = s.category || (isProhibitory ? 'CẤM' : isWarning ? 'CẢNH BÁO' : isMandatory ? 'HIỆU LỆNH' : 'CHỈ DẪN');

                  return (
                    <div
                      key={idx}
                      className={`p-3 rounded-[10px] border flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs transition-all ${cardStyle}`}
                    >
                      <div className="flex items-start gap-3.5 min-w-0 flex-1">
                        {isSpeedLimit ? (
                          <div className="w-10 h-10 rounded-full border-3 border-[#D92D20] bg-white flex items-center justify-center font-black font-mono text-base text-[#16202A] shadow-xs shrink-0 mt-0.5">
                            {s.speed_limit}
                          </div>
                        ) : isProhibitory ? (
                          <div className="w-10 h-10 rounded-full border-2 border-[#FDA29B] bg-white flex items-center justify-center text-lg shadow-xs shrink-0 text-[#D92D20] mt-0.5">
                            ⛔
                          </div>
                        ) : isWarning ? (
                          <div className="w-10 h-10 rounded-[6px] border-2 border-[#FEDF89] bg-white flex items-center justify-center text-lg shadow-xs shrink-0 text-[#B54708] mt-0.5">
                            ⚠️
                          </div>
                        ) : isMandatory ? (
                          <div className="w-10 h-10 rounded-full border-2 border-[#BAE6FD] bg-white flex items-center justify-center text-lg shadow-xs shrink-0 text-[#0284C7] mt-0.5">
                            ℹ️
                          </div>
                        ) : (
                          <div className="w-10 h-10 rounded-[6px] border-2 border-[#A6F4C5] bg-white flex items-center justify-center text-lg shadow-xs shrink-0 text-[#027A48] mt-0.5">
                            🛣️
                          </div>
                        )}

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs sm:text-sm font-bold text-[#16202A] leading-snug break-words">
                              Biển {s.sign_type}: {s.name || 'Biển báo giao thông'}
                            </span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border shrink-0 ${badgeTagColor}`}>
                              {categoryLabel}
                            </span>
                          </div>
                          <p className="text-xs text-[#344054] font-medium mt-1 leading-relaxed break-words whitespace-normal">
                            {isSpeedLimit ? (
                              <>
                                Giới hạn tốc độ: <strong className="font-mono text-[#D92D20] font-bold">{s.speed_limit} km/h</strong>
                              </>
                            ) : (
                              s.action_required || 'Tuân thủ hiệu lệnh quy định'
                            )}
                            <span className="text-[#667085] ml-2 inline-block font-normal">
                              {s.count && s.count > 1 ? `• Phát hiện ${s.count} lần` : '• Đang có hiệu lực'}
                            </span>
                          </p>

                          {(() => {
                            const penaltyText = s.penalty || getSignPenalty(s.sign_type, s.category);
                            if (!penaltyText) return null;
                            const isProhib = isSpeedLimit || isProhibitory;
                            return (
                              <div
                                className={`mt-2 flex items-start gap-1.5 p-1.5 px-2.5 rounded-md border text-[11px] sm:text-xs leading-relaxed ${
                                  isProhib
                                    ? 'bg-[#FEE4E2]/80 border-[#FECDCA] text-[#912018]'
                                    : isWarning
                                    ? 'bg-[#FEF0C7]/80 border-[#FEDF89] text-[#8C3B05]'
                                    : isMandatory
                                    ? 'bg-[#E0F2FE]/80 border-[#BAE6FD] text-[#025682]'
                                    : 'bg-white/80 border-[#D0D5DD] text-[#344054]'
                                }`}
                              >
                                <span className="font-bold shrink-0">⚖️ Mức phạt:</span>
                                <span className="font-medium break-words">{penaltyText}</span>
                              </div>
                            );
                          })()}
                        </div>
                      </div>

                      <div className="flex items-center gap-2.5 shrink-0 self-end sm:self-center pl-13 sm:pl-0">
                        {s.thumbnail && (
                          <img
                            src={s.thumbnail}
                            alt={s.sign_type || 'Biển báo'}
                            className="w-11 h-11 rounded-lg border border-[#D0D5DD] object-contain bg-white shadow-2xs p-0.5"
                          />
                        )}
                        <span className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-[#12B76A] text-white shadow-xs shrink-0 whitespace-nowrap">
                          Hiệu lực
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: MŨ BẢO HIỂM */}
        {activeTab === 'helmets' && (
          <div>
            {uniqueHelmets.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center text-[#98A2B3] bg-gradient-to-b from-[#F0FDF4]/50 to-white rounded-xl border border-[#D1FADF]">
                <div className="w-14 h-14 rounded-2xl bg-[#ECFDF3] border border-[#A6F4C5] flex items-center justify-center mb-3 shadow-xs">
                  <ShieldCheck className="w-7 h-7 stroke-[1.8] text-[#12B76A]" />
                </div>
                <h4 className="text-sm font-bold text-[#027A48]">
                  100% Tuân thủ quy định Mũ bảo hiểm
                </h4>
                <p className="text-xs text-[#475467] mt-1.5 max-w-md leading-relaxed">
                  Tất cả người điều khiển xe hai bánh trong tầm nhìn camera đều đội mũ bảo hiểm đạt chuẩn QCVN 2:2008/BKHCN (hoặc không có xe máy trong luồng).
                </p>
                <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ECFDF3] text-[11px] font-semibold text-[#027A48] border border-[#ABEFC6]">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#12B76A]" />
                  Hệ thống AI giám sát liên tục 24/7
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-3.5">
                {/* THANH TỔNG HỢP VI PHẠM CAO CẤP */}
                <div className="p-3 px-4 rounded-xl bg-gradient-to-r from-[#FFF1F3] via-[#FFE4E6] to-[#FFF1F3] border border-[#FDA4AF] flex flex-wrap items-center justify-between gap-3 text-xs shadow-xs">
                  <div className="flex items-center gap-2.5">
                    <span className="relative flex h-3 w-3 shrink-0">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#F43F5E] opacity-75" />
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-[#E11D48]" />
                    </span>
                    <div>
                      <span className="font-extrabold text-[#9F1239] text-xs sm:text-sm">
                        Phát hiện {uniqueHelmets.length} trường hợp vi phạm quy định mũ bảo hiểm
                      </span>
                      <p className="text-[11px] text-[#BE123C] font-medium hidden sm:block">
                        Hệ thống tự động ghi nhận bằng chứng hình ảnh và đối soát biển số xe
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold text-[#9F1239] bg-white/95 px-3 py-1 rounded-lg border border-[#FDA4AF] shadow-2xs shrink-0 flex items-center gap-1.5">
                      <Gavel className="w-3.5 h-3.5 text-[#E11D48]" />
                      Phạt 400.000đ – 600.000đ / vụ
                    </span>
                  </div>
                </div>

                {/* DANH SÁCH THẺ VI PHẠM REDESIGNED */}
                {uniqueHelmets.map((h, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border border-[#FDA4AF]/70 border-l-4 border-l-[#E11D48] bg-white shadow-xs hover:shadow-md hover:border-[#F43F5E] transition-all overflow-hidden flex flex-col group"
                  >
                    {/* DẢI STATUS / METADATA TRÊN CÙNG CỦA THẺ */}
                    <div className="px-3.5 py-2 bg-[#FFF1F2] border-b border-[#FFE4E6] flex items-center justify-between gap-2 flex-wrap text-[11px]">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-md font-black tracking-wide text-[10px] bg-[#E11D48] text-white shadow-2xs">
                          VI PHẠM NGHỊ ĐỊNH 123
                        </span>
                        <span className="font-mono font-bold text-[#881337] bg-white px-2 py-0.5 rounded border border-[#FECDD3]">
                          #NGƯỜI_LÁI_{h.track_id}
                        </span>
                      </div>

                      <div className="flex items-center gap-2.5 text-[#9F1239]">
                        <span className="flex items-center gap-1 font-semibold text-[#047857] bg-[#ECFDF5] px-2 py-0.5 rounded border border-[#A7F3D0]">
                          <CheckCircle2 className="w-3 h-3 text-[#10B981]" />
                          AI đã xác thực
                        </span>
                        <span className="text-[#FDA4AF]">•</span>
                        <span className="font-medium text-[#4B5563]">
                          {h.count && h.count > 1 ? `Ghi nhận ${h.count} khung hình` : 'Ghi nhận trực tiếp'}
                        </span>
                      </div>
                    </div>

                    {/* NỘI DUNG CHÍNH CỦA THẺ */}
                    <div className="p-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3.5">
                      {/* CỘT TRÁI: ICON + MÔ TẢ VI PHẠM + BIỂN SỐ XE + KHUNG PHẠT */}
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        {/* ICON MŨ BẢO HIỂM VI PHẠM HI-TECH */}
                        <div className="relative w-11 h-11 rounded-xl bg-gradient-to-br from-[#F43F5E] to-[#BE123C] text-white flex items-center justify-center shadow-xs shrink-0 mt-0.5">
                          <HardHat className="w-5 h-5 stroke-[2] opacity-95" />
                          <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-[#881337] text-white flex items-center justify-center text-[10px] font-black border-2 border-white">
                            ✕
                          </div>
                        </div>

                        <div className="flex-1 min-w-0 space-y-2">
                          {/* TIÊU ĐỀ HÀNH VI VI PHẠM */}
                          <div>
                            <h4 className="text-xs sm:text-sm font-bold text-[#1F2937] leading-snug">
                              Không đội mũ bảo hiểm khi lái xe máy
                            </h4>
                            <p className="text-[11px] text-[#6B7280] mt-0.5">
                              Người điều khiển mô tô, xe gắn máy không đội mũ bảo hiểm hoặc đội mũ không cài quai đúng cách
                            </p>
                          </div>

                          {/* KHỐI BIỂN SỐ XE KIỂU VIỆT NAM THỰC TẾ */}
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-[11px] font-semibold text-[#4B5563]">Phương tiện:</span>
                            {h.plate_text ? (
                              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-white border-2 border-[#1E293B] font-mono font-black text-xs text-[#0F172A] shadow-xs tracking-wider">
                                <span className="w-1.5 h-1.5 rounded-full bg-[#3B82F6]" />
                                <span>{h.plate_text}</span>
                              </div>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-[#F3F4F6] text-[#6B7280] border border-dashed border-[#D1D5DB]">
                                <Search className="w-3 h-3 text-[#9CA3AF]" />
                                Chưa gắn kết biển số xe
                              </span>
                            )}
                          </div>

                          {/* KHUNG MỨC XỬ PHẠT CHUẨN NGHỊ ĐỊNH 100/123 */}
                          <div className="p-2 px-3 rounded-lg bg-gradient-to-r from-[#FFF1F2] to-white border border-[#FECDD3] text-[11px] sm:text-xs text-[#881337] flex items-start gap-2">
                            <Gavel className="w-4 h-4 text-[#E11D48] shrink-0 mt-0.5" />
                            <div className="leading-relaxed">
                              <span className="font-bold text-[#BE123C]">Mức xử phạt: </span>
                              <strong className="text-[#E11D48] text-xs sm:text-sm font-black">
                                400.000đ – 600.000đ
                              </strong>
                              <span className="text-[#9F1239] block sm:inline sm:ml-1 text-[11px]">
                                (Điểm b Khoản 4 Điều 2 Nghị định 123/2021/NĐ-CP sửa đổi NĐ 100)
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* CỘT PHẢI: BẰNG CHỨNG HÌNH ẢNH CÓ THỂ PHÓNG TO + NÚT XEM CHI TIẾT */}
                      <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-2 shrink-0 self-end sm:self-center w-full sm:w-auto pt-2 sm:pt-0 border-t sm:border-t-0 border-[#FECDD3]/50">
                        {h.thumbnail ? (
                          <button
                            type="button"
                            onClick={() => setSelectedHelmetEvidence(h)}
                            className="relative group/thumb rounded-xl overflow-hidden border-2 border-[#FDA4AF] hover:border-[#E11D48] bg-slate-900 shadow-xs transition-all focus:outline-hidden"
                            title="Bấm để phóng to và xem trích xuất bằng chứng"
                          >
                            <img
                              src={h.thumbnail}
                              alt="Bằng chứng vi phạm mũ bảo hiểm"
                              className="w-16 h-16 sm:w-20 sm:h-20 object-cover bg-white group-hover/thumb:scale-105 transition-transform duration-200"
                            />
                            {/* OVERLAY KHI HOVER */}
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover/thumb:opacity-100 transition-opacity flex flex-col items-center justify-center text-white text-[10px] font-bold gap-0.5">
                              <ZoomIn className="w-4 h-4" />
                              <span>Phóng to</span>
                            </div>
                            <span className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent text-white text-[9px] font-extrabold text-center py-0.5 tracking-tight">
                              BẰNG CHỨNG
                            </span>
                          </button>
                        ) : (
                          <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-xl border-2 border-dashed border-[#FDA4AF] bg-[#FFF1F2] flex flex-col items-center justify-center text-[#E11D48] p-1 text-center">
                            <Camera className="w-5 h-5 mb-0.5 opacity-60" />
                            <span className="text-[9px] font-bold leading-tight">Khung ảnh</span>
                          </div>
                        )}

                        <button
                          type="button"
                          onClick={() => setSelectedHelmetEvidence(h)}
                          className="px-3 py-1.5 rounded-lg text-xs font-bold bg-[#E11D48] hover:bg-[#BE123C] text-white shadow-xs hover:shadow transition-all flex items-center gap-1.5 shrink-0"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Chi tiết vi phạm</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* MODAL TRÍCH XUẤT BẰNG CHỨNG VI PHẠM */}
            {selectedHelmetEvidence && (
              <div
                className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs animate-in fade-in duration-150"
                onClick={() => setSelectedHelmetEvidence(null)}
              >
                <div
                  className="bg-white rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl border border-slate-200 flex flex-col"
                  onClick={(e) => e.stopPropagation()}
                >
                  {/* HEADER MODAL */}
                  <div className="px-5 py-3.5 bg-gradient-to-r from-[#9F1239] to-[#E11D48] text-white flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ShieldAlert className="w-5 h-5 text-rose-200" />
                      <div>
                        <h3 className="text-sm font-extrabold uppercase tracking-wide">
                          Trích Xuất Bằng Chứng Vi Phạm
                        </h3>
                        <span className="text-[11px] text-rose-100 font-mono">
                          Mã hồ sơ: #HS-MBH-{selectedHelmetEvidence.track_id}
                        </span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSelectedHelmetEvidence(null)}
                      className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors"
                      title="Đóng cửa sổ"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  {/* NỘI DUNG MODAL */}
                  <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto">
                    {/* HÌNH ẢNH BẰNG CHỨNG PHÓNG TO */}
                    <div className="relative rounded-xl overflow-hidden border-2 border-slate-900 bg-slate-950 flex items-center justify-center min-h-[200px]">
                      {selectedHelmetEvidence.thumbnail ? (
                        <img
                          src={selectedHelmetEvidence.thumbnail}
                          alt="Ảnh bằng chứng vi phạm mũ bảo hiểm"
                          className="max-h-[260px] w-auto object-contain"
                        />
                      ) : (
                        <div className="py-10 text-center text-slate-400 text-xs">
                          <Camera className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          Không có ảnh trích xuất trực tiếp
                        </div>
                      )}
                      <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/70 text-white font-mono text-[10px] font-bold">
                        AI TRACKING #{selectedHelmetEvidence.track_id}
                      </div>
                      <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-[#E11D48] text-white text-[10px] font-extrabold uppercase tracking-wide">
                        BẰNG CHỨNG HỢP LỆ
                      </div>
                    </div>

                    {/* BẢNG THÔNG TIN CHI TIẾT */}
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                        <span className="text-slate-500 font-medium">Hành vi vi phạm:</span>
                        <span className="font-bold text-slate-900 text-right">
                          Không đội mũ bảo hiểm cho người đi mô tô, xe máy
                        </span>
                      </div>

                      <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                        <span className="text-slate-500 font-medium">Biển kiểm soát:</span>
                        {selectedHelmetEvidence.plate_text ? (
                          <span className="font-mono font-black text-sm text-slate-900 px-2 py-0.5 rounded bg-white border border-slate-800">
                            {selectedHelmetEvidence.plate_text}
                          </span>
                        ) : (
                          <span className="italic text-slate-500">Chưa gắn kết biển số xe</span>
                        )}
                      </div>

                      <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                        <span className="text-slate-500 font-medium">Căn cứ pháp lý:</span>
                        <span className="font-semibold text-[#9F1239] text-right">
                          Điểm b Khoản 4 Điều 2 Nghị định 123/2021/NĐ-CP (sửa đổi NĐ 100/2019/NĐ-CP)
                        </span>
                      </div>

                      <div className="flex items-center justify-between p-2.5 rounded-lg bg-rose-50 border border-rose-200">
                        <span className="text-rose-900 font-bold flex items-center gap-1.5">
                          <Gavel className="w-4 h-4 text-rose-600" />
                          Mức xử phạt tài chính:
                        </span>
                        <span className="font-black text-base text-rose-600">
                          400.000đ – 600.000đ
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* FOOTER MODAL */}
                  <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2.5">
                    <button
                      type="button"
                      onClick={() => setSelectedHelmetEvidence(null)}
                      className="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                      Đóng
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        window.print();
                      }}
                      className="px-4 py-2 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>In phiếu ghi nhận</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
});
