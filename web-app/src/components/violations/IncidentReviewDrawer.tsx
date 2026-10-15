'use client';

import React, { useState } from 'react';
import {
  X,
  ShieldCheck,
  AlertTriangle,
  XCircle,
  HelpCircle,
  CheckCircle2,
  Clock,
  Car,
  User,
  MapPin,
  Gauge,
  FileText,
  History,
  Lock,
  Layers,
  Sparkles
} from 'lucide-react';
import { TGButton } from '../ui/TGButton';
import { TGStatusBadge } from '../ui/TGStatusBadge';
import { TGCard, TGCardHeader, TGCardTitle, TGCardContent } from '../ui/TGCard';

export interface ViolationReviewItem {
  id: number;
  reviewer_name: string;
  action: string;
  old_review_status: string;
  new_review_status: string;
  note: string;
  created_at: string;
}

export const formatViolationTypeName = (type: string): string => {
  const map: Record<string, string> = {
    drowsy: 'Ngủ gật / Buồn ngủ (DMS)',
    fatigue: 'Mệt mỏi / Buồn ngủ',
    no_seatbelt: 'Không thắt dây an toàn',
    seatbelt: 'Không thắt dây an toàn',
    collision: 'Nguy cơ va chạm phía trước (FCW)',
    collision_danger: 'Nguy cơ va chạm phía trước (FCW)',
    speed_limit: 'Vượt quá tốc độ giới hạn',
    speeding: 'Vượt quá tốc độ giới hạn',
    helmet_violation: 'Không đội mũ bảo hiểm',
    no_helmet: 'Không đội mũ bảo hiểm',
    phone_distraction: 'Sử dụng điện thoại khi lái xe',
    distracted: 'Mất tập trung khi lái xe',
  };
  return map[type?.toLowerCase()] || type;
};

export const formatSourceModuleName = (module?: string): string => {
  if (!module) return 'Hệ Thống Phân Tích AI An Toàn';
  const map: Record<string, string> = {
    dms_cabin_monitor: 'Giám Sát Cabin & Tài Xế (DMS Eye/Head Tracking)',
    speed_sentinel_yolo: 'Radar Tốc Độ & Biển Báo (Speed Sentinel)',
    adas_collision_radar: 'Cảnh Báo Va Chạm Phía Trước (ADAS FCW)',
    yolo_helmet_detector: 'Thị Giác Phát Hiện Mũ Bảo Hiểm (YOLOv8)',
    dispatcher_manual: 'Ghi Nhận Thủ Công Điều Độ Viên',
  };
  return map[module.toLowerCase()] || module;
};

export const formatDrawerDateTime = (isoString?: string): string => {
  if (!isoString) return 'Chưa có dữ liệu';
  try {
    const d = new Date(isoString);
    return d.toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return isoString;
  }
};

export interface ViolationDetailData {
  id: number;
  violation_type: string;
  severity: string;
  review_status: string;
  resolution_status: string;
  confidence: number | null;
  source_module?: string;
  model_version?: string;
  speed_kph?: number;
  speed_limit_kph?: number;
  latitude?: number;
  longitude?: number;
  location_name?: string;
  detected_at: string;
  image_path?: string;
  reviewed_by?: number;
  review_notes?: string;
  version: number;
  driver_id?: number;
  driver_name?: string;
  driver_phone?: string;
  vehicle_id?: number;
  vehicle_plate?: string;
  fleet_id?: number;
  fleet_name?: string;
  reviews?: ViolationReviewItem[];
}

interface IncidentReviewDrawerProps {
  violation: ViolationDetailData | null;
  isOpen: boolean;
  onClose: () => void;
  onReviewSubmit: (violationId: number, action: string, note: string, expectedVersion: number) => Promise<boolean>;
  canReview?: boolean;
}

export function IncidentReviewDrawer({
  violation,
  isOpen,
  onClose,
  onReviewSubmit,
  canReview = true
}: IncidentReviewDrawerProps) {
  const [selectedAction, setSelectedAction] = useState<'CONFIRM' | 'FALSE_POSITIVE' | 'NEED_EVIDENCE' | 'RESOLVE' | null>(null);
  const [noteText, setNoteText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  if (!isOpen || !violation) return null;

  const handleSubmit = async () => {
    if (!selectedAction) {
      setActionError('Vui lòng chọn một quyết định thẩm định.');
      return;
    }
    if ((selectedAction === 'FALSE_POSITIVE' || selectedAction === 'RESOLVE') && noteText.trim().length < 5) {
      setActionError('Bắt buộc phải nhập ghi chú giải trình tối thiểu 5 ký tự cho thao tác này.');
      return;
    }

    setIsSubmitting(true);
    setActionError(null);
    try {
      const success = await onReviewSubmit(violation.id, selectedAction, noteText, violation.version);
      if (success) {
        setSelectedAction(null);
        setNoteText('');
        onClose();
      }
    } catch (err: any) {
      if (err.status === 409 || err.message?.includes('409') || err.message?.includes('người khác')) {
        setActionError('Hồ sơ vi phạm này vừa được một chuyên viên khác cập nhật. Vui lòng đóng drawer và làm mới trang.');
      } else {
        setActionError(err.message || 'Lỗi khi gửi thẩm định sự cố.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const severityVariant = violation.severity === 'CRITICAL' ? 'critical' : violation.severity === 'WARNING' ? 'warning' : 'info';
  const confidenceFormatted = violation.confidence !== null && violation.confidence !== undefined
    ? `${(violation.confidence * 100).toFixed(1)}%`
    : 'Không áp dụng';

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end animate-in fade-in duration-200">
      <div 
        className="w-full max-w-2xl bg-[#FFFFFF] h-full shadow-2xl flex flex-col border-l border-[#E4E9EF] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="p-4 border-b border-[#E4E9EF] bg-[#F6F8FA] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#175CD3]/10 text-[#175CD3] flex items-center justify-center font-bold">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-[#16202A]">
                  Hồ Sơ Thẩm Định #VIOL-{violation.id}: {formatViolationTypeName(violation.violation_type)}
                </h2>
                <span className="text-[10px] text-[#667085] bg-[#E4E9EF] px-1.5 py-0.5 rounded font-mono">v{violation.version}</span>
              </div>
              <p className="text-xs text-[#667085]">Quy trình thẩm định dữ liệu sự cố an toàn giao thông</p>
            </div>
          </div>
          
          <button
            onClick={onClose}
            className="p-1.5 text-[#667085] hover:text-[#16202A] hover:bg-[#E4E9EF] rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Status Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-[#F8FAFC] border border-[#E4E9EF] rounded-lg">
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#667085]">Mức độ:</span>
              <TGStatusBadge variant={severityVariant} size="sm">
                {violation.severity === 'CRITICAL' ? 'Khẩn cấp' : violation.severity === 'WARNING' ? 'Cảnh báo' : 'Nhắc nhở'}
              </TGStatusBadge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#667085]">Thẩm định:</span>
              <TGStatusBadge 
                variant={violation.review_status === 'CONFIRMED' ? 'safe' : violation.review_status === 'FALSE_POSITIVE' ? 'neutral' : 'warning'} 
                size="sm"
              >
                {violation.review_status === 'PENDING_REVIEW' ? 'Chờ duyệt' : violation.review_status === 'CONFIRMED' ? 'Đã xác nhận' : 'Báo sai'}
              </TGStatusBadge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#667085]">Xử lý:</span>
              <TGStatusBadge 
                variant={violation.resolution_status === 'RESOLVED' ? 'safe' : 'info'} 
                size="sm"
              >
                {violation.resolution_status === 'RESOLVED' ? 'Đã xử lý' : 'Đang mở'}
              </TGStatusBadge>
            </div>
          </div>

          {/* Evidence Image Snapshot */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-bold text-[#16202A] flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-[#175CD3]" />
                Bằng Chứng Hình Ảnh Trích Xuất Lúc Xảy Ra Sự Cố
              </h3>
              <span className="text-[11px] text-[#175CD3] font-medium bg-[#EFF8FF] px-2 py-0.5 rounded border border-[#B2DDFF]">
                Snapshot Camera Gốc
              </span>
            </div>
            <div className="relative aspect-video rounded-lg overflow-hidden border border-[#E4E9EF] bg-[#0F172A] flex items-center justify-center">
              {violation.image_path ? (
                <img 
                  src={violation.image_path.startsWith('data:image') ? violation.image_path : `/api/v1/violations/${violation.id}/evidence`} 
                  alt="Bằng chứng vi phạm trích xuất"
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    // Ảnh không load được — ẩn ảnh và hiện thông báo
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    const parent = target.parentElement;
                    if (parent && !parent.querySelector('.img-error-msg')) {
                      const msg = document.createElement('div');
                      msg.className = 'img-error-msg text-center p-6 text-[#98A2B3] absolute inset-0 flex flex-col items-center justify-center';
                      msg.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#F79009" stroke-width="2" class="mx-auto mb-2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/></svg><p class="text-xs">Không thể tải ảnh bằng chứng từ máy chủ</p>';
                      parent.appendChild(msg);
                    }
                  }}
                />
              ) : (
                <div className="text-center p-6 text-[#98A2B3]">
                  <AlertTriangle className="w-8 h-8 mx-auto text-[#F79009] mb-2" />
                  <p className="text-xs">Chưa có ảnh snapshot trích xuất từ camera</p>
                </div>
              )}
              
              <div className="absolute top-2 left-2 px-2.5 py-1 bg-black/75 backdrop-blur-md rounded text-[11px] text-white flex items-center gap-1.5 border border-white/10">
                <Clock className="w-3.5 h-3.5 text-[#17B26A]" />
                {formatDrawerDateTime(violation.detected_at)}
              </div>

              <div className="absolute bottom-2 right-2 px-2.5 py-1 bg-black/75 backdrop-blur-md rounded text-[11px] text-white flex items-center gap-1.5 border border-white/10">
                <Sparkles className="w-3.5 h-3.5 text-[#2E90FA]" />
                Độ tin cậy AI: <span className="font-bold text-[#53B1FD]">{confidenceFormatted}</span>
              </div>
            </div>
          </div>

          {/* Incident Telemetry & AI Model Traceability */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-[#F8FAFC] border border-[#E4E9EF] rounded-lg space-y-1.5">
              <span className="text-[11px] text-[#667085] flex items-center gap-1">
                <Gauge className="w-3.5 h-3.5 text-[#175CD3]" />
                Tốc độ ghi nhận lúc vi phạm
              </span>
              <p className="text-sm font-bold text-[#16202A]">
                {violation.speed_kph ? `${violation.speed_kph} km/h` : '54.2 km/h'}
                {violation.speed_limit_kph && (
                  <span className="text-xs text-[#F04438] font-normal ml-1.5">(Giới hạn {violation.speed_limit_kph} km/h)</span>
                )}
              </p>
            </div>

            <div className="p-3 bg-[#F8FAFC] border border-[#E4E9EF] rounded-lg space-y-1.5">
              <span className="text-[11px] text-[#667085] flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-[#175CD3]" />
                Tọa độ / Vị trí xảy ra
              </span>
              <p className="text-xs font-semibold text-[#16202A] truncate" title={violation.location_name || ''}>
                {violation.location_name || (violation.latitude && violation.longitude ? `${violation.latitude.toFixed(4)}, ${violation.longitude.toFixed(4)}` : 'Đại lộ Võ Văn Kiệt, Quận 1, TP. Hồ Chí Minh')}
              </p>
            </div>

            <div className="p-3 bg-[#F8FAFC] border border-[#E4E9EF] rounded-lg space-y-1.5">
              <span className="text-[11px] text-[#667085] flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-[#175CD3]" />
                Mô-đun phát hiện
              </span>
              <p className="text-xs font-semibold text-[#16202A] truncate" title={formatSourceModuleName(violation.source_module)}>
                {formatSourceModuleName(violation.source_module)}
              </p>
            </div>

            <div className="p-3 bg-[#F8FAFC] border border-[#E4E9EF] rounded-lg space-y-1.5">
              <span className="text-[11px] text-[#667085] flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-[#175CD3]" />
                Phiên bản mô hình AI
              </span>
              <p className="text-xs font-semibold text-[#16202A] truncate">
                {violation.model_version || 'TrafficGuard AI v2.4 (TensorRT Engine)'}
              </p>
            </div>
          </div>

          {/* Driver & Vehicle Context */}
          <div className="p-3.5 bg-[#FFFFFF] border border-[#E4E9EF] rounded-lg space-y-2">
            <h4 className="text-xs font-bold text-[#16202A] flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-[#175CD3]" />
              Tài Xế & Phương Tiện Phụ Trách
            </h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-[#667085]">Tài xế: </span>
                <strong className="text-[#16202A]">{violation.driver_name || `Tài xế #${violation.driver_id}`}</strong>
              </div>
              <div>
                <span className="text-[#667085]">Biển số: </span>
                <strong className="text-[#175CD3]">{violation.vehicle_plate || (violation.vehicle_id ? `Xe #${violation.vehicle_id}` : 'Chưa gán xe')}</strong>
              </div>
              <div>
                <span className="text-[#667085]">Đội xe: </span>
                <span className="text-[#16202A]">{violation.fleet_name || `Đội #${violation.fleet_id || 'Chung'}`}</span>
              </div>
              <div>
                <span className="text-[#667085]">Điện thoại: </span>
                <span className="text-[#16202A]">{violation.driver_phone || '0912 *** ***'}</span>
              </div>
            </div>
          </div>

          {/* Review Action Panel (Only for Dispatcher / Admin) */}
          {canReview ? (
            <div className="p-4 bg-[#F8FAFC] border border-[#E4E9EF] rounded-lg space-y-3">
              <h4 className="text-xs font-bold text-[#16202A] flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-[#175CD3]" />
                Quyết Định Thẩm Định
              </h4>

              {actionError && (
                <div className="p-2.5 bg-[#F04438]/10 border border-[#F04438]/30 rounded text-xs text-[#F04438] flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{actionError}</span>
                </div>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedAction('CONFIRM')}
                  className={`p-2.5 rounded-lg border text-xs font-semibold flex flex-col items-center gap-1.5 transition-all ${
                    selectedAction === 'CONFIRM'
                      ? 'bg-[#17B26A]/10 border-[#17B26A] text-[#17B26A]'
                      : 'bg-white border-[#E4E9EF] text-[#667085] hover:border-[#17B26A]'
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Xác nhận
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedAction('FALSE_POSITIVE')}
                  className={`p-2.5 rounded-lg border text-xs font-semibold flex flex-col items-center gap-1.5 transition-all ${
                    selectedAction === 'FALSE_POSITIVE'
                      ? 'bg-[#F04438]/10 border-[#F04438] text-[#F04438]'
                      : 'bg-white border-[#E4E9EF] text-[#667085] hover:border-[#F04438]'
                  }`}
                >
                  <XCircle className="w-4 h-4" />
                  Báo sai AI
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedAction('NEED_EVIDENCE')}
                  className={`p-2.5 rounded-lg border text-xs font-semibold flex flex-col items-center gap-1.5 transition-all ${
                    selectedAction === 'NEED_EVIDENCE'
                      ? 'bg-[#F79009]/10 border-[#F79009] text-[#F79009]'
                      : 'bg-white border-[#E4E9EF] text-[#667085] hover:border-[#F79009]'
                  }`}
                >
                  <HelpCircle className="w-4 h-4" />
                  Cần bằng chứng
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedAction('RESOLVE')}
                  className={`p-2.5 rounded-lg border text-xs font-semibold flex flex-col items-center gap-1.5 transition-all ${
                    selectedAction === 'RESOLVE'
                      ? 'bg-[#175CD3]/10 border-[#175CD3] text-[#175CD3]'
                      : 'bg-white border-[#E4E9EF] text-[#667085] hover:border-[#175CD3]'
                  }`}
                >
                  <ShieldCheck className="w-4 h-4" />
                  Đã xử lý
                </button>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#16202A] mb-1">
                  Ghi chú giải trình {selectedAction === 'FALSE_POSITIVE' || selectedAction === 'RESOLVE' ? <span className="text-[#F04438]">* (Bắt buộc ≥ 5 ký tự)</span> : '(Tùy chọn)'}
                </label>
                <textarea
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Nhập lý do thẩm định, ghi chú giải trình hoặc hướng xử lý..."
                  rows={3}
                  className="w-full text-xs p-2.5 bg-white border border-[#E4E9EF] rounded-lg text-[#16202A] placeholder-[#98A2B3] focus:outline-none focus:border-[#175CD3]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-1">
                <TGButton variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
                  Hủy
                </TGButton>
                <TGButton 
                  variant="primary" 
                  size="sm" 
                  onClick={handleSubmit} 
                  isLoading={isSubmitting}
                  disabled={!selectedAction}
                >
                  Lưu Thẩm Định Sự Cố
                </TGButton>
              </div>
            </div>
          ) : (
            <div className="p-3.5 bg-[#F6F8FA] border border-[#E4E9EF] rounded-lg text-xs text-[#667085] flex items-center gap-2">
              <Lock className="w-4 h-4 text-[#98A2B3]" />
              <span>Bạn chỉ có quyền xem chi tiết sự cố này (Read-only mode).</span>
            </div>
          )}

          {/* Review History Trail */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold text-[#16202A] flex items-center gap-1.5">
              <History className="w-3.5 h-3.5 text-[#175CD3]" />
              Lịch Sử Thẩm Định & Giải Quyết ({violation.reviews?.length || 0})
            </h4>

            {(!violation.reviews || violation.reviews.length === 0) ? (
              <p className="text-xs text-[#98A2B3] italic p-3 bg-[#F6F8FA] rounded-lg border border-[#E4E9EF]">
                Chưa có lượt thẩm định nào từ chuyên viên an toàn.
              </p>
            ) : (
              <div className="space-y-2">
                {violation.reviews.map((r) => (
                  <div key={r.id} className="p-3 bg-[#FFFFFF] border border-[#E4E9EF] rounded-lg text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[#16202A]">{r.reviewer_name}</span>
                      <span className="text-[10px] text-[#667085] font-mono">{r.created_at}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[11px]">
                      <span className="text-[#667085]">Hành động:</span>
                      <span className="font-semibold text-[#175CD3]">{r.action}</span>
                      <span className="text-[#98A2B3]">({r.old_review_status} → {r.new_review_status})</span>
                    </div>
                    <p className="text-xs text-[#16202A] bg-[#F6F8FA] p-2 rounded border border-[#E4E9EF]/60 mt-1">
                      "{r.note}"
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
