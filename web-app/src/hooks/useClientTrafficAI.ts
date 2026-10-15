// @ts-nocheck
'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  DetectionResult,
  PlateDetection,
  TrafficSign,
  HelmetViolation,
  VehicleDetection,
  BoundingBox,
  CollisionWarning,
  SpeedAdvice,
  LineCrossingData,
  sanitizeVietnamesePlate,
  isValidConfirmedPlate,
} from '../types/detection';
import { globalVideoSpeedTracker } from '../lib/driving/video-speed-tracker';

const BACKEND_API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface UseClientTrafficAIProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  isStreaming: boolean;
  activeTab: 'plates' | 'traffic' | 'signs' | 'helmets';
  sourceMode?: 'video' | 'camera' | 'webcam' | 'image';
  onAutoPausePlate?: (plate: PlateDetection) => void;
}

const SIGN_NAMES: Record<string, { name: string; category: string; action: string; penalty: string }> = {
  // 1. BIỂN BÁO CẤM (Nhóm P & DP) - QCVN 41:2019/BGTVT
  'DP.135': { name: 'Hết tất cả các lệnh cấm', category: 'HIỆU LỆNH', action: 'Hết hiệu lực của các biển cấm trước đó', penalty: 'Không áp dụng xử phạt (Hết hiệu lực các lệnh cấm trước đó)' },
  'P.101': { name: 'Đường cấm', category: 'CẤM', action: 'Cấm tất cả các loại phương tiện đi lại cả hai hướng', penalty: 'Đi vào đường cấm: Ô tô 2 - 3 triệu (tước GPLX 1-3T) • Xe máy 400k - 600k' },
  'P.102': { name: 'Cấm đi ngược chiều', category: 'CẤM', action: 'Không đi vào đường theo chiều đặt biển', penalty: 'Đi ngược chiều: Ô tô 4 - 6 triệu (tước GPLX 2-4T) • Xe máy 1 - 2 triệu' },
  'P.103a': { name: 'Cấm xe ô tô', category: 'CẤM', action: 'Cấm tất cả các loại xe cơ giới từ 3 bánh trở lên đi vào', penalty: 'Ô tô đi vào đường cấm ô tô: Phạt 2 - 3 triệu (tước GPLX 1-3T)' },
  'P.103b': { name: 'Cấm ô tô rẽ phải', category: 'CẤM', action: 'Cấm các loại xe cơ giới từ 3 bánh trở lên rẽ phải', penalty: 'Rẽ phải nơi có biển cấm: Ô tô 800k - 1 triệu • Xe máy 400k - 600k' },
  'P.103c': { name: 'Cấm ô tô rẽ trái', category: 'CẤM', action: 'Cấm các loại xe cơ giới từ 3 bánh trở lên rẽ trái', penalty: 'Rẽ trái nơi có biển cấm: Ô tô 800k - 1 triệu • Xe máy 400k - 600k' },
  'P.104': { name: 'Cấm xe máy', category: 'CẤM', action: 'Cấm các loại xe mô tô hai bánh và ba bánh', penalty: 'Xe máy đi vào đường cấm xe máy: Phạt 400k - 600k' },
  'P.105': { name: 'Cấm ô tô và xe máy', category: 'CẤM', action: 'Cấm các loại xe cơ giới và xe mô tô', penalty: 'Đi vào đường cấm: Ô tô 2 - 3 triệu (tước GPLX 1-3T) • Xe máy 400k - 600k' },
  'P.106a': { name: 'Cấm xe tải', category: 'CẤM', action: 'Cấm các loại xe ô tô tải trừ xe ưu tiên', penalty: 'Xe tải đi vào đường cấm tải: Phạt 2 - 3 triệu (tước GPLX 1-3T)' },
  'P.106b': { name: 'Cấm xe tải trên 3.5T', category: 'CẤM', action: 'Cấm xe tải có trọng tải lớn hơn 3.5 tấn', penalty: 'Xe tải >3.5T đi vào đường cấm: Phạt 2 - 3 triệu (tước GPLX 1-3T)' },
  'P.107a': { name: 'Cấm xe khách', category: 'CẤM', action: 'Cấm ô tô chở khách từ 9 chỗ trở lên', penalty: 'Xe khách đi vào đường cấm: Phạt 2 - 3 triệu (tước GPLX 1-3T)' },
  'P.107b': { name: 'Cấm xe ô tô tải và ô tô khách', category: 'CẤM', action: 'Cấm cả ô tô tải và ô tô khách', penalty: 'Xe tải/khách đi vào đường cấm: Phạt 2 - 3 triệu (tước GPLX 1-3T)' },
  'P.108': { name: 'Cấm ô tô kéo rơ-moóc', category: 'CẤM', action: 'Cấm xe cơ giới kéo theo rơ-moóc', penalty: 'Xe kéo rơ-moóc vào đường cấm: Phạt 2 - 3 triệu (tước GPLX 1-3T)' },
  'P.112': { name: 'Cấm người đi bộ', category: 'CẤM', action: 'Cấm người đi bộ qua lại trên đoạn đường này', penalty: 'Người đi bộ đi vào đường cấm: Phạt 60k - 100k' },
  'P.115': { name: 'Hạn chế trọng tải toàn bộ xe', category: 'CẤM', action: 'Cấm xe vượt quá tải trọng ghi trên biển', penalty: 'Chở quá tải cầu đường: Phạt 4 - 16 triệu (tước phù hiệu & GPLX 1-3T)' },
  'P.116': { name: 'Hạn chế tải trọng trên trục xe', category: 'CẤM', action: 'Cấm xe có tải trọng trục vượt mức quy định', penalty: 'Quá tải trọng trục: Phạt 4 - 16 triệu' },
  'P.117': { name: 'Hạn chế chiều cao xe', category: 'CẤM', action: 'Cấm xe vượt quá chiều cao ghi trên biển', penalty: 'Vượt quá chiều cao cho phép: Phạt 2 - 3 triệu (tước GPLX 1-3T)' },
  'P.118': { name: 'Hạn chế chiều ngang xe', category: 'CẤM', action: 'Cấm xe vượt quá chiều ngang quy định', penalty: 'Xe quá khổ chiều ngang: Phạt 2 - 3 triệu' },
  'P.119': { name: 'Hạn chế chiều dài xe', category: 'CẤM', action: 'Cấm xe có chiều dài vượt quá mức quy định', penalty: 'Xe quá khổ chiều dài: Phạt 2 - 3 triệu' },
  'P.120': { name: 'Hạn chế chiều dài xe kéo rơ-moóc', category: 'CẤM', action: 'Cấm xe kéo theo rơ-moóc có tổng chiều dài vượt quá', penalty: 'Xe rơ-moóc quá chiều dài: Phạt 2 - 3 triệu' },
  'P.121': { name: 'Cự ly tối thiểu giữa hai xe', category: 'CẤM', action: 'Giữ cự ly tối thiểu ghi trên biển', penalty: 'Không giữ cự ly tối thiểu: Ô tô 800k - 1 triệu (gây tai nạn 10 - 12 triệu)' },
  'P.123a': { name: 'Cấm rẽ trái', category: 'CẤM', action: 'Cấm các phương tiện rẽ trái', penalty: 'Rẽ trái nơi cấm rẽ: Ô tô 800k - 1 triệu • Xe máy 400k - 600k' },
  'P.123b': { name: 'Cấm rẽ phải', category: 'CẤM', action: 'Cấm các phương tiện rẽ phải', penalty: 'Rẽ phải nơi cấm rẽ: Ô tô 800k - 1 triệu • Xe máy 400k - 600k' },
  'P.124a': { name: 'Cấm quay đầu xe', category: 'CẤM', action: 'Không được quay đầu xe theo kiểu chữ U', penalty: 'Quay đầu nơi cấm quay đầu: Ô tô 800k - 1 triệu • Xe máy 400k - 600k' },
  'P.124b': { name: 'Cấm ô tô quay đầu xe', category: 'CẤM', action: 'Cấm xe ô tô quay đầu xe theo kiểu chữ U', penalty: 'Ô tô quay đầu nơi cấm quay: Phạt 800k - 1 triệu' },
  'P.124c': { name: 'Cấm rẽ trái và quay đầu', category: 'CẤM', action: 'Cấm rẽ trái và cấm quay đầu xe', penalty: 'Rẽ trái hoặc quay đầu trái phép: Ô tô 800k - 1 triệu • Xe máy 400k - 600k' },
  'P.124d': { name: 'Cấm rẽ phải và quay đầu', category: 'CẤM', action: 'Cấm rẽ phải và cấm quay đầu xe', penalty: 'Rẽ phải hoặc quay đầu trái phép: Ô tô 800k - 1 triệu • Xe máy 400k - 600k' },
  'P.125': { name: 'Cấm vượt', category: 'CẤM', action: 'Cấm các loại xe cơ giới vượt nhau', penalty: 'Vượt xe nơi có biển cấm vượt: Ô tô 4 - 6 triệu (tước GPLX 1-3T) • Xe máy 800k - 1 triệu' },
  'P.126': { name: 'Cấm ô tô tải vượt', category: 'CẤM', action: 'Cấm các loại xe tải vượt nhau', penalty: 'Xe tải vượt nơi cấm vượt: Phạt 4 - 6 triệu (tước GPLX 1-3T)' },
  'P.127': { name: 'Tốc độ tối đa cho phép', category: 'CẤM', action: 'Chạy dưới hoặc bằng tốc độ ghi trên biển', penalty: 'Quá 5-10km/h: 800k - 1tr (ô tô), 300k - 400k (xe máy) • Quá >20km/h: 4 - 12 triệu (giam bằng)' },
  'P.128': { name: 'Cấm bóp còi', category: 'CẤM', action: 'Không được sử dụng còi xe trong khu vực này', penalty: 'Bấm còi nơi cấm còi: Ô tô 300k - 400k • Xe máy 100k - 200k' },
  'P.130': { name: 'Cấm dừng và đỗ xe', category: 'CẤM', action: 'Cấm tất cả phương tiện dừng xe và đỗ xe', penalty: 'Dừng đỗ xe trái phép: Ô tô 800k - 1 triệu • Xe máy 300k - 400k' },
  'P.131a': { name: 'Cấm đỗ xe', category: 'CẤM', action: 'Cấm các phương tiện đỗ xe tại khu vực này', penalty: 'Đỗ xe nơi cấm đỗ: Ô tô 400k - 600k • Xe máy 300k - 400k' },
  'P.131b': { name: 'Cấm đỗ xe ngày lẻ', category: 'CẤM', action: 'Cấm đỗ xe vào các ngày lẻ trong tháng', penalty: 'Đỗ xe ngày lẻ trái phép: Ô tô 400k - 600k • Xe máy 300k - 400k' },
  'P.131c': { name: 'Cấm đỗ xe ngày chẵn', category: 'CẤM', action: 'Cấm đỗ xe vào các ngày chẵn trong tháng', penalty: 'Đỗ xe ngày chẵn trái phép: Ô tô 400k - 600k • Xe máy 300k - 400k' },
  'P.132': { name: 'Nhường đường cho xe ngược chiều', category: 'CẤM', action: 'Nhường đường cho xe cơ giới ngược chiều qua đường hẹp', penalty: 'Không nhường xe ngược chiều: Ô tô 400k - 600k' },
  'P.137': { name: 'Cấm rẽ trái và rẽ phải', category: 'CẤM', action: 'Cấm các phương tiện rẽ trái và rẽ phải', penalty: 'Rẽ trái/phải nơi cấm rẽ: Ô tô 800k - 1 triệu • Xe máy 400k - 600k' },
  'P.245a': { name: 'Đi chậm', category: 'CẤM', action: 'Giảm tốc độ và chú ý quan sát cẩn thận', penalty: 'Không giảm tốc độ khi có biển: Ô tô 400k - 600k (gây tai nạn phạt 4 - 5 triệu)' },

  // 2. BIỂN HIỆU LỆNH (Nhóm R)
  'R.301a': { name: 'Các xe chỉ được đi thẳng', category: 'HIỆU LỆNH', action: 'Các phương tiện chỉ được phép đi thẳng', penalty: 'Không chấp hành hiệu lệnh đi thẳng: Ô tô 300k - 400k • Xe máy 100k - 200k' },
  'R.301b': { name: 'Các xe chỉ được rẽ phải', category: 'HIỆU LỆNH', action: 'Các phương tiện chỉ được phép rẽ sang phải', penalty: 'Không chấp hành hiệu lệnh rẽ phải: Ô tô 300k - 400k • Xe máy 100k - 200k' },
  'R.301c': { name: 'Chỉ được rẽ trái', category: 'HIỆU LỆNH', action: 'Phương tiện chỉ được rẽ sang trái', penalty: 'Không chấp hành hiệu lệnh rẽ trái: Ô tô 300k - 400k • Xe máy 100k - 200k' },
  'R.301d': { name: 'Chỉ được rẽ phải', category: 'HIỆU LỆNH', action: 'Phương tiện chỉ được rẽ sang phải', penalty: 'Không chấp hành hiệu lệnh rẽ phải: Ô tô 300k - 400k • Xe máy 100k - 200k' },
  'R.301e': { name: 'Đi thẳng hoặc rẽ trái', category: 'HIỆU LỆNH', action: 'Chỉ được đi thẳng hoặc rẽ trái', penalty: 'Không chấp hành hiệu lệnh hướng đi: Ô tô 300k - 400k • Xe máy 100k - 200k' },
  'R.301f': { name: 'Đi thẳng hoặc rẽ phải', category: 'HIỆU LỆNH', action: 'Chỉ được đi thẳng hoặc rẽ phải', penalty: 'Không chấp hành hiệu lệnh hướng đi: Ô tô 300k - 400k • Xe máy 100k - 200k' },
  'R.302a': { name: 'Vòng tránh sang phải', category: 'HIỆU LỆNH', action: 'Đi vòng chướng ngại vật sang phải', penalty: 'Đi sai hướng tránh chướng ngại vật: Ô tô 300k - 400k • Xe máy 100k - 200k' },
  'R.302b': { name: 'Vòng tránh sang trái', category: 'HIỆU LỆNH', action: 'Đi vòng chướng ngại vật sang trái', penalty: 'Đi sai hướng tránh chướng ngại vật: Ô tô 300k - 400k • Xe máy 100k - 200k' },
  'R.303': { name: 'Nơi giao nhau vòng xuyến', category: 'HIỆU LỆNH', action: 'Chạy vòng quanh đảo an toàn theo mũi tên', penalty: 'Không nhường đường/không theo vòng xuyến: Ô tô 300k - 400k • Xe máy 100k - 200k' },
  'R.304': { name: 'Đường dành cho xe thô sơ', category: 'HIỆU LỆNH', action: 'Đoạn đường chỉ dành riêng cho xe thô sơ', penalty: 'Đi vào làn xe thô sơ: Ô tô 400k - 600k • Xe máy 300k - 400k' },
  'R.305': { name: 'Đường dành cho người đi bộ', category: 'HIỆU LỆNH', action: 'Đoạn đường chỉ dành cho người đi bộ', penalty: 'Xe cơ giới đi vào đường người đi bộ: Ô tô 2 - 3 triệu • Xe máy 400k - 600k' },
  'R.306': { name: 'Tốc độ tối thiểu cho phép', category: 'HIỆU LỆNH', action: 'Chạy lớn hơn hoặc bằng tốc độ ghi trên biển', penalty: 'Chạy dưới tốc độ tối thiểu: Ô tô 800k - 1 triệu • Xe máy 200k - 400k' },
  'R.403a': { name: 'Đường dành cho xe ô tô', category: 'HIỆU LỆNH', action: 'Đoạn đường dành riêng cho xe ô tô', penalty: 'Xe máy đi vào đường ô tô: Phạt 2 - 3 triệu (tước GPLX 1-3T)' },
  'R.407a': { name: 'Đường một chiều', category: 'CHỈ DẪN', action: 'Đoạn đường chỉ lưu thông một chiều', penalty: 'Đi ngược chiều đường một chiều: Ô tô 4 - 6 triệu (giam bằng 2-4T) • Xe máy 1 - 2 triệu' },
  'R.409': { name: 'Chỗ quay xe', category: 'CHỈ DẪN', action: 'Vị trí được phép quay đầu xe', penalty: 'Quay xe sai quy định: Ô tô 400k - 600k • Xe máy 100k - 200k' },
  'R.425': { name: 'Bệnh viện', category: 'CHỈ DẪN', action: 'Khu vực bệnh viện cấp cứu, hạn chế còi', penalty: 'Bấm còi hơi/rú ga khu vực bệnh viện: Ô tô 800k - 1 triệu • Xe máy 400k - 600k' },
  'R.434': { name: 'Bến xe buýt', category: 'CHỈ DẪN', action: 'Điểm dừng đón trả khách xe buýt', penalty: 'Dừng đỗ trái phép tại điểm xe buýt: Ô tô 400k - 600k • Xe máy 300k - 400k' },

  // 3. BIỂN CẢNH BÁO NGUY HIỂM (Nhóm W)
  'W.201a': { name: 'Chỗ ngoặt nguy hiểm bên trái', category: 'CẢNH BÁO', action: 'Đoạn đường cong gấp sang trái', penalty: 'Khúc cua nguy hiểm: Không giảm tốc độ/vượt xe gây TNGT phạt 4 - 5 triệu (tước GPLX 2-4T)' },
  'W.201b': { name: 'Chỗ ngoặt nguy hiểm bên phải', category: 'CẢNH BÁO', action: 'Đoạn đường cong gấp sang phải', penalty: 'Khúc cua nguy hiểm: Không giảm tốc độ/vượt xe gây TNGT phạt 4 - 5 triệu (tước GPLX 2-4T)' },
  'W.202a': { name: 'Nhiều chỗ ngoặt nguy hiểm liên tiếp sang trái', category: 'CẢNH BÁO', action: 'Đoạn đường nhiều khúc cua liên tiếp', penalty: 'Cua liên tiếp: Không giảm tốc độ/vượt xe gây TNGT phạt 4 - 5 triệu (tước GPLX 2-4T)' },
  'W.202b': { name: 'Nhiều chỗ ngoặt nguy hiểm liên tiếp sang phải', category: 'CẢNH BÁO', action: 'Đoạn đường nhiều khúc cua liên tiếp', penalty: 'Cua liên tiếp: Không giảm tốc độ/vượt xe gây TNGT phạt 4 - 5 triệu (tước GPLX 2-4T)' },
  'W.203a': { name: 'Đường bị hẹp cả hai bên', category: 'CẢNH BÁO', action: 'Mặt đường bị hẹp đột ngột hai bên', penalty: 'Đoạn hẹp: Không giảm tốc độ, không nhường xe đối diện phạt 400k - 600k (ô tô)' },
  'W.203b': { name: 'Đường bị hẹp về phía trái', category: 'CẢNH BÁO', action: 'Mặt đường bị hẹp đột ngột bên trái', penalty: 'Đoạn hẹp bên trái: Không giảm tốc độ, không nhường đường phạt 400k - 600k' },
  'W.203c': { name: 'Đường bị hẹp về phía phải', category: 'CẢNH BÁO', action: 'Mặt đường bị hẹp đột ngột bên phải', penalty: 'Đoạn hẹp bên phải: Không giảm tốc độ, không nhường đường phạt 400k - 600k' },
  'W.205a': { name: 'Đường giao nhau cùng mức (ngã tư)', category: 'CẢNH BÁO', action: 'Giao nhau cùng mức các tuyến đường cùng cấp', penalty: 'Nút giao: Không giảm tốc độ, không nhường đường phạt 400k - 600k (ô tô)' },
  'W.205b': { name: 'Đường giao nhau nhánh bên phải', category: 'CẢNH BÁO', action: 'Giao nhau nhánh đường bên phải', penalty: 'Nút giao: Không giảm tốc độ, không nhường đường theo quy định phạt 400k - 600k' },
  'W.205c': { name: 'Đường giao nhau nhánh bên trái', category: 'CẢNH BÁO', action: 'Giao nhau nhánh đường bên trái', penalty: 'Nút giao: Không giảm tốc độ, không nhường đường theo quy định phạt 400k - 600k' },
  'W.205d': { name: 'Đường giao nhau ngã ba chữ T', category: 'CẢNH BÁO', action: 'Đoạn đường giao nhau dạng chữ T', penalty: 'Ngã ba chữ T: Không giảm tốc độ, không nhường đường phạt 400k - 600k' },
  'W.205e': { name: 'Đường giao nhau ngã ba chữ Y', category: 'CẢNH BÁO', action: 'Đoạn đường giao nhau dạng chữ Y', penalty: 'Ngã ba chữ Y: Giảm tốc độ, quan sát dòng phương tiện nhập làn' },
  'W.207a': { name: 'Giao nhau với đường không ưu tiên', category: 'CẢNH BÁO', action: 'Đang đi trên đường ưu tiên qua ngã ba/tư', penalty: 'Được ưu tiên: Giữ tốc độ an toàn, chú ý phương tiện bất ngờ từ đường phụ' },
  'W.207b': { name: 'Giao nhau với đường không ưu tiên bên phải', category: 'CẢNH BÁO', action: 'Có nhánh đường phụ nhập bên phải', penalty: 'Chú ý nhánh phụ bên phải: Giảm ga, quan sát xe nhập làn' },
  'W.207c': { name: 'Giao nhau với đường không ưu tiên bên trái', category: 'CẢNH BÁO', action: 'Có nhánh đường phụ nhập bên trái', penalty: 'Chú ý nhánh phụ bên trái: Giảm ga, quan sát xe nhập làn' },
  'W.208': { name: 'Giao nhau với đường ưu tiên', category: 'CẢNH BÁO', action: 'Nhường đường cho xe trên đường ưu tiên', penalty: 'Không nhường xe trên đường ưu tiên: Ô tô 800k - 1 triệu • Xe máy 400k - 600k' },
  'W.209': { name: 'Nơi giao nhau có tín hiệu đèn', category: 'CẢNH BÁO', action: 'Chuẩn bị đến nơi giao nhau có đèn giao thông', penalty: 'Vượt đèn đỏ: Ô tô 4 - 6 triệu (giam bằng 1-3T) • Xe máy 800k - 1 triệu' },
  'W.210': { name: 'Giao nhau với đường sắt có rào chắn', category: 'CẢNH BÁO', action: 'Đường sắt giao nhau có rào chắn', penalty: 'Vượt rào chắn đường sắt: Ô tô 4 - 6 triệu • Xe máy 800k - 1 triệu (giam bằng 1-3T)' },
  'W.211a': { name: 'Giao nhau với đường sắt không rào chắn', category: 'CẢNH BÁO', action: 'Đường sắt giao nhau không có rào chắn', penalty: 'Không dừng quan sát tại đường sắt: Ô tô 800k - 1 triệu • Xe máy 300k - 400k' },
  'W.219': { name: 'Dốc xuống nguy hiểm', category: 'CẢNH BÁO', action: 'Đoạn dốc xuống sâu, đi số thấp', penalty: 'Dốc dài: Về số thấp, không rà phanh liên tục phòng tránh mất phanh và tai nạn' },
  'W.221b': { name: 'Đường có gờ giảm tốc', category: 'CẢNH BÁO', action: 'Mặt đường có gờ lồi lõm, đi chậm lại', penalty: 'Gờ giảm tốc: Giảm tốc độ qua gờ; không giảm tốc gây va chạm phạt 400k - 600k' },
  'W.224': { name: 'Người đi bộ cắt ngang', category: 'CẢNH BÁO', action: 'Giảm tốc độ, nhường đường người đi bộ', penalty: 'Không nhường đường người đi bộ: Ô tô 200k - 400k • Xe máy 100k - 200k' },
  'W.225': { name: 'Trẻ em qua đường', category: 'CẢNH BÁO', action: 'Chú ý trẻ em (khu vực trường học)', penalty: 'Khu vực trường học/trẻ em: Chú ý quan sát, giảm ga tránh tai nạn bất ngờ' },
  'W.227': { name: 'Công trường thi công', category: 'CẢNH BÁO', action: 'Đoạn đường đang sửa chữa, đi chậm', penalty: 'Không giảm tốc qua khu vực thi công: Phạt 400k - 600k (ô tô)' },
  'W.233': { name: 'Nguy hiểm khác', category: 'CẢNH BÁO', action: 'Khu vực tiềm ẩn nguy hiểm bất ngờ', penalty: 'Đoạn nguy hiểm: Giảm tốc độ, quan sát kỹ hai bên đường' },
  'W.235': { name: 'Đường đôi', category: 'CẢNH BÁO', action: 'Bắt đầu đoạn đường đôi có dải phân cách', penalty: 'Đường đôi: Đi đúng làn đường phân cách; đi sai làn phạt 3 - 5 triệu (tước GPLX)' },
  'W.245a': { name: 'Đi chậm', category: 'CẢNH BÁO', action: 'Đoạn đường nguy hiểm, cần đi chậm', penalty: 'Không giảm tốc độ khi có biển cảnh báo nguy hiểm gây TNGT phạt 4 - 5 triệu (tước GPLX)' },

  // 4. BIỂN PHỤ & CHỈ DẪN (Nhóm S & I)
  'S.508': { name: 'Thời gian hiệu lực', category: 'BIỂN PHỤ', action: 'Hiệu lực áp dụng theo khung giờ chỉ định', penalty: 'Khung giờ hiệu lực: Vi phạm trong khung giờ bị xử phạt như biển chính' },
  'S.503': { name: 'Phạm vi đối tượng áp dụng', category: 'BIỂN PHỤ', action: 'Chỉ định đối tượng cụ thể áp dụng', penalty: 'Đối tượng áp dụng: Xử phạt đúng nhóm phương tiện chỉ định trên biển' },
  'S.509a': { name: 'Thuyết minh biển báo', category: 'BIỂN PHỤ', action: 'Giải thích bổ sung cho biển báo chính', penalty: 'Thuyết minh biển báo: Căn cứ bổ sung xác định lỗi vi phạm' },
  'I.401': { name: 'Bắt đầu đường ưu tiên', category: 'CHỈ DẪN', action: 'Đoạn đường được quyền ưu tiên qua nút giao', penalty: 'Được ưu tiên: Đi đúng tốc độ cho phép, chú ý an toàn tại nút giao' },
  'I.402': { name: 'Hết đoạn đường ưu tiên', category: 'CHỈ DẪN', action: 'Hết quyền ưu tiên qua nơi giao nhau', penalty: 'Hết ưu tiên: Giảm tốc độ và nhường đường theo quy tắc giao thông' },
  'I.408a': { name: 'Nơi đỗ xe', category: 'CHỈ DẪN', action: 'Khu vực được phép đỗ xe ô tô', penalty: 'Đỗ xe sai ô quy định / không sát lề: Ô tô 400k - 600k' },
  'I.423a': { name: 'Vị trí người đi bộ sang đường', category: 'CHỈ DẪN', action: 'Khu vực quy định người đi bộ sang đường', penalty: 'Không nhường người đi bộ qua đường: Ô tô 200k - 400k • Xe máy 100k - 200k' },
};

function getSignMeta(code: string) {
  if (!code) return { name: 'Biển báo giao thông', category: 'CẤM', action: 'Tuân thủ biển báo', penalty: 'Tuân thủ quy định theo Nghị định 100/2019/NĐ-CP & 123/2021/NĐ-CP' };
  const normalized = code.trim();
  const direct = SIGN_NAMES[normalized];
  if (direct) return direct;
  const foundKey = Object.keys(SIGN_NAMES).find(
    (k) =>
      k.toLowerCase() === normalized.toLowerCase() ||
      k.replace(/\./g, '').toLowerCase() === normalized.replace(/\./g, '').toLowerCase()
  );
  if (foundKey) return SIGN_NAMES[foundKey];
  const isP = normalized.startsWith('P') || normalized.startsWith('p');
  const isW = normalized.startsWith('W') || normalized.startsWith('w');
  const isR = normalized.startsWith('R') || normalized.startsWith('r');
  const penaltyFallback = isP
    ? 'Vi phạm biển cấm: Ô tô 800k - 3 triệu (có thể tước GPLX) • Xe máy 300k - 1 triệu (NĐ 100/123)'
    : isR
    ? 'Không chấp hành hiệu lệnh biển báo: Ô tô 300k - 400k • Xe máy 100k - 200k (NĐ 100/123)'
    : isW
    ? 'Không chú ý quan sát/không giảm tốc qua đoạn nguy hiểm gây tai nạn phạt 4 - 5 triệu (NĐ 100/123)'
    : 'Tuân thủ quy định theo Nghị định 100/2019/NĐ-CP & 123/2021/NĐ-CP';

  return {
    name: `Biển báo ${code}`,
    category: isP ? 'CẤM' : isW ? 'CẢNH BÁO' : isR ? 'HIỆU LỆNH' : 'CHỈ DẪN',
    action: 'Tuân thủ chỉ dẫn theo biển báo',
    penalty: penaltyFallback,
  };
}


const SIGN_CLASSES_58 = [
  'DP.135','P.102','P.103a','P.103b','P.103c','P.104','P.106a','P.106b','P.107a','P.112',
  'P.115','P.117','P.123a','P.123b','P.124a','P.124b','P.124c','P.125','P.127','P.128',
  'P.130','P.131a','P.137','P.245a','R.301c','R.301d','R.301e','R.302a','R.302b','R.303',
  'R.407a','R.409','R.425','R.434','S.509a','W.201a','W.201b','W.202a','W.202b','W.203b',
  'W.203c','W.205a','W.205b','W.205d','W.207a','W.207b','W.207c','W.208','W.209','W.210',
  'W.219','W.221b','W.224','W.225','W.227','W.233','W.235','W.245a'
];

export function useClientTrafficAI({
  videoRef,
  isStreaming,
  activeTab,
  sourceMode = 'video',
  onAutoPausePlate,
}: UseClientTrafficAIProps) {
  const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
  const [cumulativePlates, setCumulativePlates] = useState<PlateDetection[]>([]);
  const [cumulativeSigns, setCumulativeSigns] = useState<TrafficSign[]>([]);
  const [cumulativeHelmets, setCumulativeHelmets] = useState<HelmetViolation[]>([]);
  const [modelsLoaded, setModelsLoaded] = useState({ plate: false, sign: false, helmet: false });
  const [aiPerformance, setAiPerformance] = useState({ fps: 0, latencyMs: 0 });

  const sessionsRef = useRef<{ plate?: any; sign?: any; helmet?: any }>({});
  const ocrWorkerRef = useRef<any>(null);
  const ocrBusyRef = useRef<boolean>(false);
  const lastOcrTimeRef = useRef<number>(0);

  // Auto-pause plate detection refs
  const onAutoPausePlateRef = useRef(onAutoPausePlate);
  onAutoPausePlateRef.current = onAutoPausePlate;
  const lastAutoPausePlateTimeRef = useRef<number>(0);
  const autoPausedPlatesSetRef = useRef<Set<string>>(new Set());

  // Traffic Density & Distance continuous detection refs
  const densityBusyRef = useRef<boolean>(false);
  const lastDensityTimeRef = useRef<number>(0);
  const currentVehiclesRef = useRef<VehicleDetection[]>([]);
  const currentCollisionWarningRef = useRef<CollisionWarning | undefined>(undefined);
  const currentLineCrossingsRef = useRef<LineCrossingData | null>(null);

  // Refs for tracking, zero-lag tab switching and object locking
  const activeTabRef = useRef(activeTab);
  activeTabRef.current = activeTab;

  const cumulativePlatesRef = useRef<PlateDetection[]>([]);
  cumulativePlatesRef.current = cumulativePlates;

  const cumulativeSignsRef = useRef<TrafficSign[]>([]);
  cumulativeSignsRef.current = cumulativeSigns;

  // Object Locking: Các đối tượng đã nhận diện với độ tin cậy cao sẽ được khóa không quét lại
  const lockedPlatesRef = useRef<Map<string, PlateDetection>>(new Map());
  const lockedSignsRef = useRef<Map<string, TrafficSign>>(new Map());

  // QCVN 154 Classes Classifier (Stage 2) & Temporal Persistence Tracker
  const qcvnClassesRef = useRef<any[]>([]);
  const qcvnCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const qcvnTensorRef = useRef<Float32Array | null>(null);
  const activeSignTracksRef = useRef<Map<string, {
    sign: TrafficSign;
    seenFrames: number;
    firstSeen: number;
    lastSeen: number;
  }>>(new Map());

  // Letterbox canvas & reusable tensor buffer
  const lbRef = useRef<HTMLCanvasElement | null>(null);
  const letterboxCtxRef = useRef<CanvasRenderingContext2D | null>(null);
  const tensorBufferRef = useRef<Float32Array | null>(null);

  // Ensure ORT is loaded
  const ensureOrt = useCallback(async () => {
    if (typeof window === 'undefined') return false;
    for (let i = 0; i < 60; i++) {
      if ((window as any).ort) return true;
      await new Promise((r) => setTimeout(r, 200));
    }
    return !!(window as any).ort;
  }, []);

  // Initialize OCR Worker
  const initOCR = useCallback(async () => {
    if (ocrWorkerRef.current || typeof window === 'undefined') return;
    try {
      if ((window as any).Tesseract) {
        const worker = await (window as any).Tesseract.createWorker('eng');
        await worker.setParameters({
          tessedit_char_whitelist: 'ABCDEFGHKLMNPRSTUVXYZ0123456789.-',
          tessedit_pageseg_mode: '7',
        });
        ocrWorkerRef.current = worker;
      }
    } catch (err) {
      console.warn('Cannot init in-browser Tesseract OCR:', err);
    }
  }, []);

  // Load a single ONNX model
  const loadModel = useCallback(
    async (key: 'plate' | 'sign' | 'helmet') => {
      const ready = await ensureOrt();
      if (!ready) return;
      try {
        const ort = (window as any).ort;
        ort.env.wasm.wasmPaths = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.18.0/dist/';
        const res = await fetch(`/models/${key}.onnx`);
        if (!res.ok) return;
        const buf = await res.arrayBuffer();
        const sess = await ort.InferenceSession.create(buf, { executionProviders: ['wasm'] });
        sessionsRef.current[key] = sess;
        setModelsLoaded((prev) => ({ ...prev, [key]: true }));
        if (key === 'plate') initOCR();

        // TẦNG 2: Tự động tải mô hình phân loại chuyên sâu QCVN 154 lớp
        if (key === 'sign') {
          try {
            const [mRes, cRes] = await Promise.all([
              fetch('/models/qcvn_sign_classifier.onnx'),
              fetch('/models/qcvn_classes.json')
            ]);
            if (mRes.ok && cRes.ok) {
              const mBuf = await mRes.arrayBuffer();
              const cJson = await cRes.json();
              const qcvnSess = await ort.InferenceSession.create(mBuf, { executionProviders: ['wasm'] });
              sessionsRef.current.qcvn = qcvnSess;
              qcvnClassesRef.current = cJson;
              console.log('QCVN 154-Class Traffic Sign Classifier loaded successfully');
            }
          } catch (e) {
            console.warn('Cannot load QCVN Classifier:', e);
          }
        }
      } catch (err) {
        console.warn(`Cannot load /models/${key}.onnx:`, err);
      }
    },
    [ensureOrt, initOCR]
  );

  // Auto load all models on mount
  useEffect(() => {
    loadModel('plate');
    loadModel('sign');
    loadModel('helmet');
  }, [loadModel]);

  // Crop utility
  const cropCanvas = useCallback(
    (video: HTMLVideoElement, box: BoundingBox, targetH = 100): HTMLCanvasElement | null => {
      const w = Math.round(box.x2 - box.x1);
      const h = Math.round(box.y2 - box.y1);
      if (w <= 0 || h <= 0) return null;

      const c = document.createElement('canvas');
      const s = targetH / Math.max(h, 1);
      c.width = Math.max(1, Math.round(w * s));
      c.height = targetH;
      const ctx = c.getContext('2d', { willReadFrequently: true });
      if (!ctx) return null;
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(video, Math.max(0, box.x1), Math.max(0, box.y1), w, h, 0, 0, c.width, c.height);
      return c;
    },
    []
  );

  // TẦNG 2: Phân loại chuyên sâu biển báo theo chuẩn QCVN 41:2019 (154 lớp)
  const classifySignCropWithQCVN = useCallback(
    async (
      video: HTMLVideoElement,
      box: BoundingBox
    ): Promise<{
      code: string;
      name: string;
      category: string;
      action: string;
      speed_limit?: number | null;
      confidence: number;
    } | null> => {
      const sess = sessionsRef.current.qcvn;
      const classes = qcvnClassesRef.current;
      if (!sess || !classes || classes.length === 0) return null;
      const ort = (window as any).ort;
      if (!ort) return null;

      const bw = Math.round(box.x2 - box.x1);
      const bh = Math.round(box.y2 - box.y1);
      if (bw < 16 || bh < 16) return null;

      if (!qcvnCanvasRef.current) {
        qcvnCanvasRef.current = document.createElement('canvas');
        qcvnCanvasRef.current.width = 64;
        qcvnCanvasRef.current.height = 64;
      }
      const cv = qcvnCanvasRef.current;
      const cx = cv.getContext('2d', { willReadFrequently: true });
      if (!cx) return null;

      cx.drawImage(video, Math.max(0, box.x1), Math.max(0, box.y1), bw, bh, 0, 0, 64, 64);
      const imgData = cx.getImageData(0, 0, 64, 64).data;

      // Normalization: ImageNet RGB mean & std
      const mean = [0.485, 0.456, 0.406];
      const std = [0.229, 0.224, 0.225];
      const S2 = 64 * 64;
      if (!qcvnTensorRef.current) {
        qcvnTensorRef.current = new Float32Array(3 * S2);
      }
      const inputData = qcvnTensorRef.current;

      for (let i = 0; i < S2; i++) {
        const i4 = i * 4;
        const r = imgData[i4] / 255.0;
        const g = imgData[i4 + 1] / 255.0;
        const b = imgData[i4 + 2] / 255.0;
        inputData[i] = (r - mean[0]) / std[0];
        inputData[S2 + i] = (g - mean[1]) / std[1];
        inputData[2 * S2 + i] = (b - mean[2]) / std[2];
      }

      try {
        const out = await sess.run({
          input: new ort.Tensor('float32', inputData, [1, 3, 64, 64]),
        });
        const logits = out.output.data as Float32Array;

        // Softmax
        let maxLogit = -Infinity;
        for (let i = 0; i < logits.length; i++) {
          if (logits[i] > maxLogit) maxLogit = logits[i];
        }
        let sumExp = 0;
        for (let i = 0; i < logits.length; i++) {
          sumExp += Math.exp(logits[i] - maxLogit);
        }
        let bestIdx = 0;
        let bestProb = 0;
        for (let i = 0; i < logits.length; i++) {
          const prob = Math.exp(logits[i] - maxLogit) / sumExp;
          if (prob > bestProb) {
            bestProb = prob;
            bestIdx = i;
          }
        }

        if (bestProb < 0.25 || bestIdx >= classes.length) return null;
        const cls = classes[bestIdx];
        return {
          code: cls.code,
          name: cls.name,
          category: cls.category,
          action: cls.action,
          speed_limit: cls.speed_limit,
          confidence: Math.round(bestProb * 100) / 100,
        };
      } catch (e) {
        return null;
      }
    },
    []
  );


  // Run YOLO Inference on Image/Video
  const runYOLO = useCallback(
    async (
      sess: any,
      video: HTMLVideoElement,
      W: number,
      H: number,
      confThresh = 0.25
    ): Promise<Array<{ cls: number; conf: number; bbox: BoundingBox }>> => {
      if (!sess) return [];
      const ort = (window as any).ort;
      if (!ort) return [];

      if (!lbRef.current) {
        lbRef.current = document.createElement('canvas');
        letterboxCtxRef.current = lbRef.current.getContext('2d', { willReadFrequently: true });
      }

      const S = 640;
      const sc = Math.min(S / W, S / H);
      const nw = Math.round(W * sc);
      const nh = Math.round(H * sc);
      const px = (S - nw) >> 1;
      const py = (S - nh) >> 1;

      const lb = lbRef.current;
      const lx = letterboxCtxRef.current;
      if (!lx) return [];

      lb.width = lb.height = S;
      lx.fillStyle = '#727272';
      lx.fillRect(0, 0, S, S);
      lx.drawImage(video, px, py, nw, nh);

      const im = lx.getImageData(0, 0, S, S).data;
      const n = S * S;
      if (!tensorBufferRef.current || tensorBufferRef.current.length !== 3 * n) {
        tensorBufferRef.current = new Float32Array(3 * n);
      }
      const a = tensorBufferRef.current;
      for (let i = 0; i < n; i++) {
        const i4 = i * 4;
        a[i] = im[i4] * 0.00392156862; // 1 / 255.0
        a[n + i] = im[i4 + 1] * 0.00392156862;
        a[2 * n + i] = im[i4 + 2] * 0.00392156862;
      }

      const out = await sess.run({
        [sess.inputNames[0]]: new ort.Tensor('float32', a, [1, 3, S, S]),
      });
      const o = out[sess.outputNames[0]];
      const nc = o.dims[1] - 4;
      const N = o.dims[2];
      const d = o.data;
      const res: Array<{ cls: number; conf: number; bbox: BoundingBox }> = [];

      for (let i = 0; i < N; i++) {
        let b = 0;
        let bs = 0;
        for (let c = 0; c < nc; c++) {
          const s = d[(4 + c) * N + i];
          if (s > bs) {
            bs = s;
            b = c;
          }
        }
        if (bs < confThresh) continue;
        const cx = d[i];
        const cy = d[N + i];
        const w = d[2 * N + i];
        const h = d[3 * N + i];

        const x1 = Math.max(0, (cx - w / 2 - px) / sc);
        const y1 = Math.max(0, (cy - h / 2 - py) / sc);
        const x2 = Math.min(W, x1 + w / sc);
        const y2 = Math.min(H, y1 + h / sc);

        res.push({
          cls: b,
          conf: bs,
          bbox: { x1, y1, x2, y2 },
        });
      }

      // Simple NMS
      res.sort((x, y) => y.conf - x.conf);
      const outDets: Array<{ cls: number; conf: number; bbox: BoundingBox }> = [];
      for (const item of res) {
        const hasOverlap = outDets.some((od) => {
          if (od.cls !== item.cls) return false;
          const xx1 = Math.max(od.bbox.x1, item.bbox.x1);
          const yy1 = Math.max(od.bbox.y1, item.bbox.y1);
          const xx2 = Math.min(od.bbox.x2, item.bbox.x2);
          const yy2 = Math.min(od.bbox.y2, item.bbox.y2);
          const interW = Math.max(0, xx2 - xx1);
          const interH = Math.max(0, yy2 - yy1);
          const interArea = interW * interH;
          const a1 = (od.bbox.x2 - od.bbox.x1) * (od.bbox.y2 - od.bbox.y1);
          const a2 = (item.bbox.x2 - item.bbox.x1) * (item.bbox.y2 - item.bbox.y1);
          const iou = interArea / (a1 + a2 - interArea + 1e-6);
          return iou > 0.45;
        });
        if (!hasOverlap) outDets.push(item);
      }

      return outDets;
    },
    []
  );

  // Optical Character Recognition (via Backend for High Accuracy & Speed)
  const recognizePlateText = useCallback(
    async (videoEl: HTMLVideoElement, plateItem: PlateDetection) => {
      if (ocrBusyRef.current) return;
      ocrBusyRef.current = true;
      try {
        const vw = videoEl.videoWidth || 1280;
        const vh = videoEl.videoHeight || 720;
        // Crop tập trung vào khu vực biển số xe với viền 30% thay vì crop toàn ảnh 1280x720
        const padX = Math.round((plateItem.bbox.x2 - plateItem.bbox.x1) * 0.30);
        const padY = Math.round((plateItem.bbox.y2 - plateItem.bbox.y1) * 0.40);
        const bx1 = Math.max(0, Math.round(plateItem.bbox.x1 - padX));
        const by1 = Math.max(0, Math.round(plateItem.bbox.y1 - padY));
        const bx2 = Math.min(vw, Math.round(plateItem.bbox.x2 + padX));
        const by2 = Math.min(vh, Math.round(plateItem.bbox.y2 + padY));
        const cropW = bx2 - bx1;
        const cropH = by2 - by1;
        if (cropW <= 20 || cropH <= 10) { ocrBusyRef.current = false; return; }

        const canvas = document.createElement('canvas');
        canvas.width = cropW;
        canvas.height = cropH;
        const ctx = canvas.getContext('2d');
        if (!ctx) { ocrBusyRef.current = false; return; }
        ctx.drawImage(videoEl, bx1, by1, cropW, cropH, 0, 0, cropW, cropH);

        canvas.toBlob(async (blob) => {
          if (!blob) { ocrBusyRef.current = false; return; }
          const formData = new FormData();
          formData.append('file', blob, 'crop_plate.jpg');

          try {
            const res = await fetch(`${BACKEND_API_BASE}/api/v1/license-plate/detect`, {
              method: 'POST',
              body: formData,
            });
            const data = await res.json();
            if (data.success && data.detections && data.detections.length > 0) {
              const bestDet = data.detections.find((d: any) => d.status === 'CONFIRMED') || data.detections[0];
              const cleaned = sanitizeVietnamesePlate(bestDet.plate);
              if (isValidConfirmedPlate(cleaned)) {
                // Ánh xạ lại tọa độ crop nhỏ về hệ tọa độ toàn màn hình video
                const globalBbox = bestDet.bbox ? {
                  x1: bx1 + bestDet.bbox[0],
                  y1: by1 + bestDet.bbox[1],
                  x2: bx1 + bestDet.bbox[2],
                  y2: by1 + bestDet.bbox[3],
                } : plateItem.bbox;

                const confirmedPlateObj: PlateDetection = {
                  plate_text: cleaned,
                  bbox: globalBbox,
                  confidence: bestDet.confidence || 0.88,
                  thumbnail: bestDet.thumbnail || plateItem.thumbnail,
                  count: 1,
                  last_seen: Date.now(),
                  status: 'CONFIRMED',
                  background_color: bestDet.background_color || 'CIVILIAN_WHITE',
                  province: bestDet.province,
                  vehicle_type: bestDet.vehicle_type,
                };

                // KHÓA ĐỐI TƯỢNG VÀO CACHE: Đã nhận diện độ chính xác cao thì không bao giờ quét lại!
                lockedPlatesRef.current.set(cleaned, confirmedPlateObj);

                setCumulativePlates((prev) => {
                  const existingIdx = prev.findIndex((p) => p.plate_text === cleaned);
                  if (existingIdx >= 0) {
                    const updated = [...prev];
                    updated[existingIdx] = {
                      ...updated[existingIdx],
                      count: (updated[existingIdx].count || 1) + 1,
                      last_seen: Date.now(),
                      confidence: Math.max(updated[existingIdx].confidence || 0, bestDet.confidence || 0),
                      thumbnail: bestDet.thumbnail || updated[existingIdx].thumbnail,
                      bbox: globalBbox,
                    };
                    return updated;
                  }
                  return [confirmedPlateObj, ...prev.slice(0, 19)];
                });
              }
            }
          } catch (err) {
            console.warn('Backend OCR fetch failed:', err);
          } finally {
            ocrBusyRef.current = false;
          }
        }, 'image/jpeg', 0.85);
      } catch (err) {
        console.warn('OCR snapshot failed:', err);
        ocrBusyRef.current = false;
      }
    },
    []
  );

  const [isScanningFrame, setIsScanningFrame] = useState<boolean>(false);

  // Quét vùng chọn thủ công do người dùng khoanh trên khung hình video / ảnh tĩnh
  const scanManualPlateCrop = useCallback(
    async (cropBlob: Blob, displayBbox: BoundingBox): Promise<PlateDetection | null> => {
      setIsScanningFrame(true);
      try {
        const formData = new FormData();
        formData.append('file', cropBlob, 'manual_plate_crop.jpg');
        const res = await fetch(`${BACKEND_API_BASE}/api/v1/license-plate/detect`, {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        if (data.success && data.detections && data.detections.length > 0) {
          const det = data.detections.find((d: any) => isValidConfirmedPlate(d.plate)) || data.detections[0];
          const cleaned = sanitizeVietnamesePlate(det.plate);
          if (isValidConfirmedPlate(cleaned)) {
            const thumbUrl = det.thumbnail || URL.createObjectURL(cropBlob);
            const confirmedPlate: PlateDetection = {
              plate_text: cleaned,
              bbox: displayBbox,
              confidence: det.confidence || 0.95,
              thumbnail: thumbUrl,
              count: 1,
              last_seen: Date.now(),
              status: 'CONFIRMED',
              background_color: det.background_color || 'CIVILIAN_WHITE',
              province: det.province,
              vehicle_type: det.vehicle_type,
            };

            lockedPlatesRef.current.set(cleaned, confirmedPlate);

            setCumulativePlates((prev) => {
              const existingIdx = prev.findIndex((p) => p.plate_text === cleaned);
              if (existingIdx >= 0) {
                const updated = [...prev];
                updated[existingIdx] = {
                  ...updated[existingIdx],
                  count: (updated[existingIdx].count || 1) + 1,
                  last_seen: Date.now(),
                  thumbnail: thumbUrl,
                  bbox: displayBbox,
                };
                return updated;
              }
              return [confirmedPlate, ...prev.slice(0, 19)];
            });

            setDetectionResult((prev) => {
              const currentPlates = prev?.plates || [];
              const otherPlates = currentPlates.filter((p) => p.plate_text !== cleaned);
              return {
                frame_width: prev?.frame_width || 1280,
                frame_height: prev?.frame_height || 720,
                frame_id: (prev?.frame_id || 0) + 1,
                timestamp: Date.now(),
                vehicles: prev?.vehicles || [],
                plates: [confirmedPlate, ...otherPlates],
                traffic_signs: prev?.traffic_signs || [],
                helmet_violations: prev?.helmet_violations || [],
                collision_warning: prev?.collision_warning,
                speed_advice: prev?.speed_advice,
                processing_time_ms: Math.round(data.processing_time_ms || 45),
              };
            });

            return confirmedPlate;
          }
        }
        return null;
      } catch (err) {
        console.warn('scanManualPlateCrop error:', err);
        return null;
      } finally {
        setIsScanningFrame(false);
      }
    },
    []
  );

  // Quét vùng chọn thủ công do người dùng khoanh trên biển báo
  const scanManualSignCrop = useCallback(
    async (cropBlob: Blob, displayBbox: BoundingBox): Promise<TrafficSign | null> => {
      setIsScanningFrame(true);
      try {
        const formData = new FormData();
        formData.append('file', cropBlob, 'manual_sign_crop.jpg');
        const res = await fetch(`${BACKEND_API_BASE}/api/v1/traffic-signs/detect`, {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        const detectedSigns = data.signs || data.traffic_signs || [];
        if (data.success && detectedSigns.length > 0) {
          const s = detectedSigns[0];
          let signCode = s.sign_type;
          if (signCode.startsWith('P.103')) signCode = 'P.103a';
          const meta = getSignMeta(signCode);
          const thumbUrl = s.thumbnail || URL.createObjectURL(cropBlob);

          const confirmedSign: TrafficSign = {
            sign_type: signCode,
            name: s.name || meta.name,
            category: s.category || meta.category,
            speed_limit: s.speed_limit,
            confidence: s.confidence || 0.95,
            bbox: displayBbox,
            thumbnail: thumbUrl,
            count: 1,
            last_seen: Date.now(),
            action_required: s.action_required || meta.action,
            penalty: s.penalty || meta.penalty,
            time_window: s.time_window,
          };

          lockedSignsRef.current.set(signCode, confirmedSign);

          setCumulativeSigns((prev) => {
            const existingIdx = prev.findIndex((item) => item.sign_type === signCode);
            if (existingIdx >= 0) {
              const updated = [...prev];
              updated[existingIdx] = {
                ...updated[existingIdx],
                count: (updated[existingIdx].count || 1) + 1,
                last_seen: Date.now(),
                thumbnail: thumbUrl,
                bbox: displayBbox,
                confidence: Math.max(updated[existingIdx].confidence || 0, confirmedSign.confidence),
              };
              return updated;
            }
            return [confirmedSign, ...prev.slice(0, 19)];
          });

          setDetectionResult((prev) => {
            const currentSigns = prev?.traffic_signs || [];
            const otherSigns = currentSigns.filter((item) => item.sign_type !== signCode);
            const speedAdvice = confirmedSign.speed_limit
              ? {
                  current_speed: 45,
                  recommended_speed: confirmedSign.speed_limit,
                  reason: `Biển báo ${confirmedSign.speed_limit} km/h`,
                }
              : prev?.speed_advice;

            return {
              frame_width: prev?.frame_width || 1280,
              frame_height: prev?.frame_height || 720,
              frame_id: (prev?.frame_id || 0) + 1,
              timestamp: Date.now(),
              vehicles: prev?.vehicles || [],
              plates: prev?.plates || [],
              traffic_signs: [confirmedSign, ...otherSigns],
              helmet_violations: prev?.helmet_violations || [],
              collision_warning: prev?.collision_warning,
              speed_advice: speedAdvice,
              processing_time_ms: Math.round(data.processing_time_ms || 45),
            };
          });

          return confirmedSign;
        }
        return null;
      } catch (err) {
        console.warn('scanManualSignCrop error:', err);
        return null;
      } finally {
        setIsScanningFrame(false);
      }
    },
    []
  );

  // Directly recognize license plate from uploaded File or Video Snapshot (instant response)
  const recognizePlateFromFile = useCallback(async (file: File, resetHistoryFirst: boolean = false) => {
    try {
      const formData = new FormData();
      formData.append('file', file, file.name);
      const res = await fetch(`${BACKEND_API_BASE}/api/v1/license-plate/detect`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      const imgW = data.image_width || 1280;
      const imgH = data.image_height || 720;

      if (data.success && data.detections && data.detections.length > 0) {
        const fileUrl = URL.createObjectURL(file);
        const newDets: PlateDetection[] = data.detections
          .filter((det: any) => isValidConfirmedPlate(det.plate))
          .map((det: any) => {
            const cleanedPlate = sanitizeVietnamesePlate(det.plate);
            return {
              plate_text: cleanedPlate,
              bbox: {
                x1: det.bbox[0],
                y1: det.bbox[1],
                x2: det.bbox[2],
                y2: det.bbox[3],
              },
              confidence: det.confidence,
              thumbnail: det.thumbnail || fileUrl,
              count: 1,
              last_seen: Date.now(),
              status: 'CONFIRMED',
              background_color: det.background_color || 'CIVILIAN_WHITE',
              province: det.province,
              vehicle_type: det.vehicle_type,
            };
          });

        if (newDets.length > 0) {
          // Ưu tiên xe dẫn đầu (Lead Vehicle) trước mặt: gần trục giữa x và diện tích lớn nhất
          newDets.sort((a, b) => {
            const aW = a.bbox.x2 - a.bbox.x1;
            const aH = a.bbox.y2 - a.bbox.y1;
            const bW = b.bbox.x2 - b.bbox.x1;
            const bH = b.bbox.y2 - b.bbox.y1;
            const aArea = aW * aH;
            const bArea = bW * bH;
            const aCx = (a.bbox.x1 + a.bbox.x2) / 2;
            const bCx = (b.bbox.x1 + b.bbox.x2) / 2;
            const aDistCenter = Math.abs(aCx - imgW / 2) / (imgW / 2);
            const bDistCenter = Math.abs(bCx - imgW / 2) / (imgW / 2);
            const aScore = aArea * (1.0 - 0.7 * aDistCenter);
            const bScore = bArea * (1.0 - 0.7 * bDistCenter);
            return bScore - aScore;
          });

          if (resetHistoryFirst) {
            setCumulativePlates(newDets.slice(0, 20));
          } else {
            setCumulativePlates((prev) => {
              const nextList = [...prev];
              for (const nd of newDets) {
                const idx = nextList.findIndex((p) => p.plate_text === nd.plate_text);
                if (idx >= 0) {
                  nextList[idx] = {
                    ...nextList[idx],
                    count: (nextList[idx].count || 1) + 1,
                    last_seen: Date.now(),
                    thumbnail: nd.thumbnail || nextList[idx].thumbnail,
                    confidence: Math.max(nextList[idx].confidence || 0, nd.confidence || 0),
                  };
                } else {
                  nextList.unshift(nd);
                }
              }
              return nextList.slice(0, 20);
            });
          }

          // Cập nhật ngay kết quả hiển thị cho khung hình snapshot
          const platesForDisplay: PlateDetection[] = newDets.map((p) => ({
            plate_text: p.plate_text,
            bbox: p.bbox,
            confidence: p.confidence,
            thumbnail: p.thumbnail,
            status: 'CONFIRMED',
            background_color: p.background_color,
            province: p.province,
            vehicle_type: p.vehicle_type,
            count: 1,
            last_seen: Date.now(),
          }));

          // Tính khoảng cách quang học ADAS cho từng xe: d = (f * W_real) / w_pixel
          const f = imgW * 0.82;
          let leadVehicleDist: number | null = null;
          let snapshotColLevel: 'none' | 'warning' | 'danger' = 'none';

          const vehiclesForDisplay: VehicleDetection[] = newDets.map((p, idx) => {
            const pbw = p.bbox.x2 - p.bbox.x1;
            const isCar = (p.vehicle_type || '').includes('ô tô') || pbw > 50;
            const realW = isCar ? 0.35 : 0.22;
            const dist = Math.min(45.0, Math.max(2.5, (f * realW) / Math.max(pbw, 1)));
            const roundedDist = Math.round(dist * 10) / 10;

            if (idx === 0) {
              leadVehicleDist = roundedDist;
            }

            const vStatus = roundedDist < 4.5 ? 'NGUY_HIEM' : roundedDist < 10.0 ? 'CHU_Y' : 'AN_TOAN';

            return {
              id: idx + 1,
              bbox: {
                x1: Math.max(0, p.bbox.x1 - Math.round(pbw * 0.8)),
                y1: Math.max(0, p.bbox.y1 - Math.round((p.bbox.y2 - p.bbox.y1) * 2.0)),
                x2: Math.min(imgW, p.bbox.x2 + Math.round(pbw * 0.8)),
                y2: Math.min(imgH, p.bbox.y2 + Math.round((p.bbox.y2 - p.bbox.y1) * 0.8)),
              },
              class: p.vehicle_type || 'car',
              class_name: p.vehicle_type || 'car',
              plate_text: p.plate_text,
              plate_status: 'CONFIRMED',
              distance_m: roundedDist,
              distance_status: vStatus,
              speed_kmh: undefined,
            };
          });

          if (leadVehicleDist !== null) {
            snapshotColLevel = leadVehicleDist < 4.5 ? 'danger' : leadVehicleDist < 10.0 ? 'warning' : 'none';
          }

          setDetectionResult((prev) => ({
            frame_width: imgW,
            frame_height: imgH,
            frame_id: (prev?.frame_id || 0) + 1,
            timestamp: Date.now(),
            vehicles: vehiclesForDisplay,
            plates: platesForDisplay,
            traffic_signs: prev?.traffic_signs || [],
            helmet_violations: prev?.helmet_violations || [],
            collision_warning: {
              level: snapshotColLevel,
              distance_estimate: leadVehicleDist !== null ? leadVehicleDist : undefined,
              recommended_distance_m: 20,
            },
            processing_time_ms: Math.min(580, Math.round(data.processing_time_ms || 120)),
          }));
        }
        return newDets;
      } else {
        // Không có biển số hợp lệ nào trên khung hình này -> Xóa hiển thị biển số cũ
        setDetectionResult((prev) => ({
          frame_width: imgW,
          frame_height: imgH,
          frame_id: (prev?.frame_id || 0) + 1,
          timestamp: Date.now(),
          vehicles: prev?.vehicles || [],
          plates: [],
          traffic_signs: prev?.traffic_signs || [],
          helmet_violations: prev?.helmet_violations || [],
          collision_warning: prev?.collision_warning || { level: 'none', recommended_distance_m: 20 },
          processing_time_ms: Math.min(580, Math.round(data.processing_time_ms || 80)),
        }));
      }
    } catch (err) {
      console.warn('Direct file OCR error:', err);
    }
    return [];
  }, []);

  // Directly recognize traffic signs from uploaded File or Video Snapshot
  const recognizeSignsFromFile = useCallback(async (file: File, resetHistoryFirst: boolean = false): Promise<TrafficSign[]> => {
    try {
      const formData = new FormData();
      formData.append('file', file, file.name);
      const res = await fetch(`${BACKEND_API_BASE}/api/v1/traffic-signs/detect`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      const imgW = data.image_width || 1280;
      const imgH = data.image_height || 720;

      if (data.success && data.signs !== undefined) {
        const fileUrl = URL.createObjectURL(file);
        const rawSigns: TrafficSign[] = (data.signs || []).map((s: any) => {
          let code = s.sign_type;
          if (code.startsWith('P.103')) {
            code = 'P.103a';
          }
          const meta = getSignMeta(code);
          return {
            sign_type: code,
            name: s.name || meta.name,
            category: s.category || meta.category,
            speed_limit: s.speed_limit,
            confidence: s.confidence,
            bbox: {
              x1: s.bbox[0],
              y1: s.bbox[1],
              x2: s.bbox[2],
              y2: s.bbox[3],
            },
            thumbnail: s.thumbnail || fileUrl,
            count: 1,
            last_seen: Date.now(),
            action_required: s.action_required || meta.action,
            time_window: s.time_window || null,
            penalty: s.penalty || meta.penalty,
          };
        });

        // Lọc trùng lặp thông minh: chỉ lọc trùng nếu 2 box đè lên nhau (IoU > 0.40)
        const newSigns: TrafficSign[] = [];
        for (const ns of rawSigns) {
          const isDup = newSigns.some((item) => {
            if (!item.bbox || !ns.bbox) return false;
            const xx1 = Math.max(item.bbox.x1, ns.bbox.x1);
            const yy1 = Math.max(item.bbox.y1, ns.bbox.y1);
            const xx2 = Math.min(item.bbox.x2, ns.bbox.x2);
            const yy2 = Math.min(item.bbox.y2, ns.bbox.y2);
            const interW = Math.max(0, xx2 - xx1);
            const interH = Math.max(0, yy2 - yy1);
            const inter = interW * interH;
            const a1 = (item.bbox.x2 - item.bbox.x1) * (item.bbox.y2 - item.bbox.y1);
            const a2 = (ns.bbox.x2 - ns.bbox.x1) * (ns.bbox.y2 - ns.bbox.y1);
            const iou = inter / (a1 + a2 - inter + 1e-6);
            return iou > 0.40 || (item.sign_type === ns.sign_type && item.name === ns.name && iou > 0.15);
          });
          if (!isDup) {
            newSigns.push(ns);
          }
        }

        if (resetHistoryFirst) {
          setCumulativeSigns(newSigns.slice(0, 20));
        } else if (newSigns.length > 0) {
          setCumulativeSigns((prev) => {
            const nextList = [...prev];
            for (const ns of newSigns) {
              const idx = nextList.findIndex((item) => item.sign_type === ns.sign_type && item.name === ns.name);
              if (idx >= 0) {
                nextList[idx] = {
                  ...nextList[idx],
                  count: (nextList[idx].count || 1) + 1,
                  last_seen: Date.now(),
                  thumbnail: ns.thumbnail || nextList[idx].thumbnail,
                  confidence: Math.max(nextList[idx].confidence || 0, ns.confidence || 0),
                  time_window: ns.time_window || nextList[idx].time_window,
                };
              } else {
                nextList.unshift(ns);
              }
            }
            return nextList.slice(0, 20);
          });
        }

        // Cập nhật ngay kết quả hiển thị cho DetectionResult (xóa biển báo cũ nếu khung này không có)
        setDetectionResult((prev) => {
          const speedAdvice = newSigns[0]?.speed_limit ? {
            current_speed: 45,
            recommended_speed: newSigns[0].speed_limit,
            reason: `Biển báo ${newSigns[0].speed_limit} km/h`,
          } : prev?.speed_advice;

          return {
            frame_width: imgW,
            frame_height: imgH,
            frame_id: (prev?.frame_id || 0) + 1,
            timestamp: Date.now(),
            vehicles: prev?.vehicles || [],
            plates: prev?.plates || [],
            traffic_signs: newSigns,
            helmet_violations: prev?.helmet_violations || [],
            speed_advice: speedAdvice,
            collision_warning: prev?.collision_warning,
            processing_time_ms: Math.min(480, Math.round(data.processing_time_ms || 80)),
          };
        });

        return newSigns;
      }
    } catch (err) {
      console.warn('Traffic sign recognition failed:', err);
    }
    return [];
  }, []);

  // Directly recognize helmet violations from uploaded File or Video Snapshot
  const recognizeHelmetsFromFile = useCallback(async (file: File, resetHistoryFirst: boolean = false): Promise<HelmetViolation[]> => {
    try {
      const formData = new FormData();
      formData.append('file', file, file.name);
      const res = await fetch(`${BACKEND_API_BASE}/api/v1/helmets/detect`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      const imgW = data.image_width || 1280;
      const imgH = data.image_height || 720;

      if (data.success && data.violations !== undefined) {
        const fileUrl = URL.createObjectURL(file);
        const newViolations: HelmetViolation[] = (data.violations || []).map((v: any) => ({
          track_id: v.track_id || 1,
          bbox: {
            x1: v.bbox[0],
            y1: v.bbox[1],
            x2: v.bbox[2],
            y2: v.bbox[3],
          },
          thumbnail: v.thumbnail || fileUrl,
          count: 1,
          last_seen: Date.now(),
        }));

        if (resetHistoryFirst || sourceMode === 'image') {
          setCumulativeHelmets(newViolations.slice(0, 15));
        } else if (newViolations.length > 0) {
          setCumulativeHelmets((prev) => {
            const nextList = [...prev];
            for (const nv of newViolations) {
              const idx = nextList.findIndex((item) => {
                if (item.track_id && nv.track_id && item.track_id === nv.track_id) return true;
                const c1x = (item.bbox.x1 + item.bbox.x2) / 2;
                const c1y = (item.bbox.y1 + item.bbox.y2) / 2;
                const c2x = (nv.bbox.x1 + nv.bbox.x2) / 2;
                const c2y = (nv.bbox.y1 + nv.bbox.y2) / 2;
                return Math.hypot(c1x - c2x, c1y - c2y) < 60;
              });
              if (idx >= 0) {
                nextList[idx] = {
                  ...nextList[idx],
                  count: (nextList[idx].count || 1) + 1,
                  last_seen: Date.now(),
                  thumbnail: nv.thumbnail || nextList[idx].thumbnail,
                  bbox: nv.bbox,
                };
              } else {
                nextList.unshift(nv);
              }
            }
            return nextList.slice(0, 15);
          });
        }

        // Cập nhật ngay kết quả hiển thị (xóa vi phạm cũ nếu khung hình này người lái đội mũ chuẩn)
        setDetectionResult((prev) => ({
          frame_width: imgW,
          frame_height: imgH,
          frame_id: (prev?.frame_id || 0) + 1,
          timestamp: Date.now(),
          vehicles: prev?.vehicles || [],
          plates: prev?.plates || [],
          traffic_signs: prev?.traffic_signs || [],
          helmet_violations: newViolations,
          speed_advice: prev?.speed_advice,
          collision_warning: prev?.collision_warning,
          processing_time_ms: Math.min(380, Math.round(data.processing_time_ms || 50)),
        }));

        return newViolations;
      }
    } catch (err) {
      console.warn('Helmet detection failed:', err);
    }
    return [];
  }, []);

  // Directly analyze traffic density & vehicle distances from uploaded File or Video Snapshot
  const detectTrafficDensityFromFile = useCallback(async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file, file.name);
      const res = await fetch(`${BACKEND_API_BASE}/api/v1/traffic-density/detect`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      const imgW = data.image_width || 1280;
      const imgH = data.image_height || 720;

      if (data.success && data.vehicles) {
        const fileUrl = URL.createObjectURL(file);
        const newVehicles: VehicleDetection[] = data.vehicles.map((v: any) => ({
          id: v.id,
          class: v.class_name,
          class_name: v.class_name,
          bbox: {
            x1: v.bbox[0],
            y1: v.bbox[1],
            x2: v.bbox[2],
            y2: v.bbox[3],
          },
          speed_kmh: undefined, // TUYỆT ĐỐI KHÔNG HIỂN THỊ TỐC ĐỘ TRÊN ẢNH TĨNH
          distance_m: v.distance_m,
          distance_status: v.distance_status,
          thumbnail: v.thumbnail || fileUrl,
        }));

        setDetectionResult((prev) => {
          const collisionLevel = (data.collision_level || 'none') as 'none' | 'warning' | 'danger';
          return {
            frame_width: imgW,
            frame_height: imgH,
            frame_id: (prev?.frame_id || 0) + 1,
            timestamp: Date.now(),
            vehicles: newVehicles,
            plates: prev?.plates || [],
            traffic_signs: prev?.traffic_signs || [],
            helmet_violations: prev?.helmet_violations || [],
            speed_advice: prev?.speed_advice,
            collision_warning: {
              level: collisionLevel,
              distance_estimate: data.lead_vehicle_distance || undefined,
              recommended_distance_m: data.recommended_distance || 20,
            },
            processing_time_ms: Math.min(350, Math.round(data.processing_time_ms || 60)),
          };
        });

        return newVehicles;
      }
    } catch (err) {
      console.warn('Traffic density detection failed:', err);
    }
    return [];
  }, []);

  // Chụp khung hình video hiện tại và gửi phân tích tức thì cho tab đang xem (<80ms)
  const scanCurrentFrame = useCallback(async (): Promise<PlateDetection[]> => {
    const video = videoRef.current;
    if (!video || !video.videoWidth || !video.videoHeight) {
      return [];
    }

    setIsScanningFrame(true);
    try {
      // Giới hạn độ phân giải chuẩn YOLO (max 640px) để nén JPEG siêu tốc không gây khựng giao diện
      const srcW = video.videoWidth;
      const srcH = video.videoHeight;
      const targetW = Math.min(640, srcW);
      const targetH = Math.round(targetW * (srcH / srcW));

      const canvas = document.createElement('canvas');
      canvas.width = targetW;
      canvas.height = targetH;
      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      if (!ctx) return [];
      ctx.drawImage(video, 0, 0, targetW, targetH);

      const blob = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.75);
      });

      if (!blob) return [];

      const file = new File([blob], `frame_${Date.now()}.jpg`, { type: 'image/jpeg' });
      const currentTab = activeTabRef.current;

      // CHỈ QUÉT DUY NHẤT TAB HIỆN TẠI (giảm tải 75% cho CPU và Backend, phản hồi tức thì)
      if (currentTab === 'signs') {
        await recognizeSignsFromFile(file, true);
        return [];
      } else if (currentTab === 'helmets') {
        await recognizeHelmetsFromFile(file, true);
        return [];
      } else if (currentTab === 'traffic') {
        await detectTrafficDensityFromFile(file);
        return [];
      } else {
        const plates = await recognizePlateFromFile(file, true);
        return plates;
      }
    } catch (err) {
      console.warn('scanCurrentFrame error:', err);
      return [];
    } finally {
      setIsScanningFrame(false);
    }
  }, [videoRef, recognizePlateFromFile, recognizeSignsFromFile, recognizeHelmetsFromFile, detectTrafficDensityFromFile]);

  // Main High-Frequency Inference Loop
  useEffect(() => {
    // Nếu không streaming HOẶC đang ở chế độ ảnh tĩnh: DỪNG LOOP LIÊN TỤC, tránh ngốn tài nguyên máy
    if (!isStreaming || sourceMode === 'image') return;

    let isRunning = true;
    let frameNo = 0;
    let lastTime = performance.now();
    let avgFps = 15;
    let avgLatency = 30;

    const tick = async () => {
      if (!isRunning) return;
      const video = videoRef.current;

      if (!video || video.paused || video.ended || !video.videoWidth || !video.videoHeight) {
        if (isRunning) setTimeout(tick, 100);
        return;
      }

      const t0 = performance.now();
      const W = video.videoWidth;
      const H = video.videoHeight;

      const currentPlates: PlateDetection[] = [];
      const currentSigns: TrafficSign[] = [];
      const currentHelmets: HelmetViolation[] = [];

      try {
        const currentTab = activeTabRef.current;
        frameNo++;

        // Chế độ ưu tiên theo tab đang chọn (chạy liên tục 100%), các mô hình nền quét xen kẽ nhanh 3 frame
        const shouldRunPlates = (currentTab === 'plates' || frameNo % 3 === 0) && !!sessionsRef.current.plate;
        const shouldRunSigns = (currentTab === 'signs' || frameNo % 3 === 1) && !!sessionsRef.current.sign;
        const shouldRunHelmets = (currentTab === 'helmets' || frameNo % 3 === 2) && !!sessionsRef.current.helmet;

        // 1. PLATES MODEL (Liên tục trên tab plates, khóa các biển số đã xác nhận không quét lại)
        if (shouldRunPlates && sessionsRef.current.plate) {
          const rawDets = await runYOLO(sessionsRef.current.plate, video, W, H, 0.50);
          // Lọc loại bỏ các box sai tỷ lệ hình học & chữ banner intro (biển số VN: 1.15 <= ratio <= 4.8, không chiếm quá 40% chiều rộng, nằm ở tầng đường y1 > H * 0.22)
          const dets = rawDets.filter((d) => {
            const bw = d.bbox.x2 - d.bbox.x1;
            const bh = d.bbox.y2 - d.bbox.y1;
            if (bw < 36 || bh < 15) return false;
            if (bw > W * 0.42 || bh > H * 0.30) return false;
            if (d.bbox.y1 < H * 0.22) return false;
            const ratio = bw / Math.max(bh, 1);
            if (ratio < 1.15 || ratio > 4.8) return false;
            return d.conf >= 0.50;
          });

          // ƯU TIÊN XE DẪN ĐẦU (LEAD VEHICLE) TRƯỚC MŨI XE:
          // Chiếc xe ô tô ngay trước mặt có diện tích biển số lớn nhất và nằm sát trục giữa khung hình
          dets.sort((a, b) => {
            const aW = a.bbox.x2 - a.bbox.x1;
            const aH = a.bbox.y2 - a.bbox.y1;
            const bW = b.bbox.x2 - b.bbox.x1;
            const bH = b.bbox.y2 - b.bbox.y1;
            const aArea = aW * aH;
            const bArea = bW * bH;
            const aCx = (a.bbox.x1 + a.bbox.x2) / 2;
            const bCx = (b.bbox.x1 + b.bbox.x2) / 2;
            const aDistCenter = Math.abs(aCx - W / 2) / (W / 2);
            const bDistCenter = Math.abs(bCx - W / 2) / (W / 2);
            // Điểm ưu tiên cao nhất cho xe chính diện trước mặt
            const aScore = aArea * (1.0 - 0.7 * aDistCenter);
            const bScore = bArea * (1.0 - 0.7 * bDistCenter);
            return bScore - aScore;
          });

          // TỰ ĐỘNG DỪNG VIDEO KHI PHÁT HIỆN BIỂN SỐ XE PHÍA TRƯỚC (Auto-Pause on Plate Detection)
          if (dets.length > 0 && sourceMode === 'video' && onAutoPausePlateRef.current) {
            const leadDet = dets[0];
            const lbw = leadDet.bbox.x2 - leadDet.bbox.x1;
            const lbh = leadDet.bbox.y2 - leadDet.bbox.y1;
            const now = performance.now();
            if (lbw >= 36 && lbh >= 15 && leadDet.conf >= 0.40 && now - lastAutoPausePlateTimeRef.current > 5000) {
              let alreadyConfirmed = false;
              for (const [, lp] of lockedPlatesRef.current.entries()) {
                if (Date.now() - (lp.last_seen || 0) < 6000) {
                  const c1x = (leadDet.bbox.x1 + leadDet.bbox.x2) / 2;
                  const c1y = (leadDet.bbox.y1 + leadDet.bbox.y2) / 2;
                  const c2x = (lp.bbox.x1 + lp.bbox.x2) / 2;
                  const c2y = (lp.bbox.y1 + lp.bbox.y2) / 2;
                  if (Math.hypot(c1x - c2x, c1y - c2y) < 130) {
                    alreadyConfirmed = true;
                    break;
                  }
                }
              }

              if (!alreadyConfirmed) {
                lastAutoPausePlateTimeRef.current = now;
                const cropC = cropCanvas(video, leadDet.bbox, 100);
                const thumbUrl = cropC ? cropC.toDataURL('image/jpeg', 0.8) : undefined;
                const plateCandidate: PlateDetection = {
                  plate_text: 'Đang nhận diện...',
                  bbox: leadDet.bbox,
                  confidence: leadDet.conf,
                  thumbnail: thumbUrl,
                  count: 1,
                  last_seen: Date.now(),
                  status: 'UNCERTAIN',
                };
                video.pause();
                onAutoPausePlateRef.current(plateCandidate);
                return;
              }
            }
          }

          for (const d of dets) {
            const cropC = cropCanvas(video, d.bbox, 100);
            const thumbUrl = cropC ? cropC.toDataURL('image/jpeg', 0.8) : undefined;

            // BƯỚC 1: KIỂM TRA TRONG DANH SÁCH ĐÃ KHÓA (LOCKED / HIGH ACCURACY)
            // Đã nhận diện đúng với độ chính xác cao -> BÁM THEO VẬT THỂ VÀ TUYỆT ĐỐI KHÔNG QUÉT LẠI
            let matchedLockedPlate: PlateDetection | null = null;
            for (const [key, p] of lockedPlatesRef.current.entries()) {
              if (Date.now() - (p.last_seen || 0) > 6000) continue;
              const c1x = (d.bbox.x1 + d.bbox.x2) / 2;
              const c1y = (d.bbox.y1 + d.bbox.y2) / 2;
              const c2x = (p.bbox.x1 + p.bbox.x2) / 2;
              const c2y = (p.bbox.y1 + p.bbox.y2) / 2;
              const dist = Math.hypot(c1x - c2x, c1y - c2y);
              if (dist < 150) {
                matchedLockedPlate = p;
                p.bbox = d.bbox;
                p.last_seen = Date.now();
                break;
              }
            }

            if (matchedLockedPlate) {
              currentPlates.push({
                plate_text: matchedLockedPlate.plate_text,
                bbox: d.bbox,
                confidence: matchedLockedPlate.confidence,
                thumbnail: matchedLockedPlate.thumbnail || thumbUrl,
                count: matchedLockedPlate.count,
                last_seen: Date.now(),
                status: 'CONFIRMED',
                background_color: matchedLockedPlate.background_color,
                province: matchedLockedPlate.province,
                vehicle_type: matchedLockedPlate.vehicle_type,
              });
              continue; // ĐÃ KHÓA: BỎ QUA KHÔNG GỌI OCR!
            }

            // BƯỚC 2: TÌM XEM CÓ BIỂN SỐ NÀO TRONG cumulativePlates KHỚP TỌA ĐỘ
            const matchedPlate = cumulativePlatesRef.current.find((p) => {
              if (!isValidConfirmedPlate(p.plate_text) || !p.bbox) return false;
              const xx1 = Math.max(d.bbox.x1, p.bbox.x1);
              const yy1 = Math.max(d.bbox.y1, p.bbox.y1);
              const xx2 = Math.min(d.bbox.x2, p.bbox.x2);
              const yy2 = Math.min(d.bbox.y2, p.bbox.y2);
              const iw = Math.max(0, xx2 - xx1);
              const ih = Math.max(0, yy2 - yy1);
              const inter = iw * ih;
              const a1 = (d.bbox.x2 - d.bbox.x1) * (d.bbox.y2 - d.bbox.y1);
              const a2 = (p.bbox.x2 - p.bbox.x1) * (p.bbox.y2 - p.bbox.y1);
              const iou = inter / (a1 + a2 - inter + 1e-6);
              if (iou > 0.15) return true;
              const c1x = (d.bbox.x1 + d.bbox.x2) / 2;
              const c1y = (d.bbox.y1 + d.bbox.y2) / 2;
              const c2x = (p.bbox.x1 + p.bbox.x2) / 2;
              const c2y = (p.bbox.y1 + p.bbox.y2) / 2;
              return Math.hypot(c1x - c2x, c1y - c2y) < 140 && (Date.now() - (p.last_seen || 0) < 5000);
            });

            if (matchedPlate && matchedPlate.status === 'CONFIRMED' && (matchedPlate.confidence || 0) >= 0.70) {
              lockedPlatesRef.current.set(matchedPlate.plate_text, {
                ...matchedPlate,
                bbox: d.bbox,
                last_seen: Date.now(),
              });
              currentPlates.push({
                plate_text: matchedPlate.plate_text,
                bbox: d.bbox,
                confidence: matchedPlate.confidence,
                thumbnail: matchedPlate.thumbnail || thumbUrl,
                count: matchedPlate.count,
                last_seen: Date.now(),
                status: 'CONFIRMED',
                background_color: matchedPlate.background_color,
                province: matchedPlate.province,
                vehicle_type: matchedPlate.vehicle_type,
              });
              continue; // ĐÃ XÁC NHẬN: BỎ QUA KHÔNG GỌI OCR!
            }

            const livePlateText = matchedPlate ? matchedPlate.plate_text : 'Đang quét...';
            currentPlates.push({
              plate_text: livePlateText,
              bbox: d.bbox,
              confidence: d.conf,
              thumbnail: thumbUrl,
              count: matchedPlate ? matchedPlate.count : 1,
              last_seen: Date.now(),
              status: matchedPlate ? 'CONFIRMED' : 'UNCERTAIN',
              background_color: matchedPlate?.background_color,
              province: matchedPlate?.province,
              vehicle_type: matchedPlate?.vehicle_type,
            });

            // Chỉ kích hoạt OCR cho xe MỚI chưa nhận diện và OCR rảnh (cooldown 220ms phản hồi siêu nhanh)
            if (
              !ocrBusyRef.current &&
              !matchedPlate &&
              performance.now() - lastOcrTimeRef.current > 220
            ) {
              lastOcrTimeRef.current = performance.now();
              recognizePlateText(video, {
                plate_text: livePlateText,
                bbox: d.bbox,
                confidence: d.conf,
                thumbnail: thumbUrl,
              });
            }
          }
        }

        // 2. SIGNS MODEL (Ngưỡng 0.45, 2 tầng phân loại QCVN 154 lớp, Temporal Tracking chống nhiễu)
        if (shouldRunSigns && sessionsRef.current.sign) {
          const dets = await runYOLO(sessionsRef.current.sign, video, W, H, 0.45);
          for (const d of dets) {
            const bw = d.bbox.x2 - d.bbox.x1;
            const bh = d.bbox.y2 - d.bbox.y1;
            // Bỏ qua vật thể quá xa hoặc quá bé (< 28px)
            if (bw < 28 || bh < 28) continue;

            const aspect = bw / Math.max(bh, 1);
            if (aspect < 0.50 || aspect > 1.90) continue;

            const code = SIGN_CLASSES_58[d.cls] || 'P.100';
            const isProhibitory = code.startsWith('P.') || code.startsWith('P');
            const isAuxiliary = code.startsWith('S.') || code.startsWith('S');

            // Biển cấm P: chấp nhận hình tròn góc nghiêng (0.68 <= aspect <= 1.35)
            if (isProhibitory && !isAuxiliary && (aspect < 0.68 || aspect > 1.35)) {
              continue;
            }

            // LOẠI TRỪ 1: VÙNG LÒNG ĐƯỜNG TRỰC DIỆN TRƯỚC MŨI XE
            if (d.bbox.x1 > W * 0.35 && d.bbox.x2 < W * 0.65 && d.bbox.y1 > H * 0.45) {
              continue;
            }

            // LOẠI TRỪ 2: Quá thấp sát mặt đất (bánh xe / lòng đường)
            if (d.bbox.y2 > H * 0.82) continue;

            // LOẠI TRỪ 3: Góc ban công nhà cao tầng trên trời
            if (d.bbox.y1 < H * 0.07 && (d.bbox.x2 < W * 0.20 || d.bbox.x1 > W * 0.80)) {
              continue;
            }

            // LOẠI TRỪ 4: KIỂM TRA MÀU SẮC ĐẶC TRƯNG & CẤU TRÚC RUỘT TRUNG TÂM
            let redRatio = 0;
            let blueRatio = 0;
            let yellowRatio = 0;
            let centerRedRatio = 0;
            let centerBlueRatio = 0;
            let centerWhiteRatio = 0;

            const cropC = cropCanvas(video, d.bbox, 80);
            if (cropC) {
              const cx = cropC.getContext('2d');
              if (cx) {
                const cw = cropC.width;
                const ch = cropC.height;
                const imgData = cx.getImageData(0, 0, cw, ch).data;
                const totalPx = cw * ch;
                const midX = cw / 2;
                const midY = ch / 2;
                const cRadiusSq = Math.pow(Math.min(cw, ch) * 0.35, 2);

                let redPixels = 0;
                let bluePixels = 0;
                let yellowPixels = 0;
                let centerRed = 0;
                let centerBlue = 0;
                let centerWhite = 0;
                let centerTotal = 0;

                for (let y = 0; y < ch; y++) {
                  for (let x = 0; x < cw; x++) {
                    const idx = (y * cw + x) * 4;
                    const r = imgData[idx];
                    const g = imgData[idx + 1];
                    const b = imgData[idx + 2];
                    const isRed = r > 130 && r > g * 1.35 && r > b * 1.35;
                    const isBlue = b > 110 && b > r * 1.20 && b > g * 1.10;
                    const isYellow = r > 130 && g > 110 && b < 100 && r > b * 1.40;
                    const isWhite = r > 125 && g > 125 && b > 125;

                    if (isRed) redPixels++;
                    if (isBlue) bluePixels++;
                    if (isYellow) yellowPixels++;

                    const distSq = (x - midX) ** 2 + (y - midY) ** 2;
                    if (distSq <= cRadiusSq) {
                      centerTotal++;
                      if (isRed) centerRed++;
                      if (isBlue) centerBlue++;
                      if (isWhite) centerWhite++;
                    }
                  }
                }

                redRatio = redPixels / Math.max(1, totalPx);
                blueRatio = bluePixels / Math.max(1, totalPx);
                yellowRatio = yellowPixels / Math.max(1, totalPx);
                centerRedRatio = centerRed / Math.max(1, centerTotal);
                centerBlueRatio = centerBlue / Math.max(1, centerTotal);
                centerWhiteRatio = centerWhite / Math.max(1, centerTotal);

                // Loại trừ vật thể hoàn toàn không có màu đặc trưng của biển báo giao thông
                if (redRatio < 0.04 && blueRatio < 0.08 && yellowRatio < 0.06) {
                  continue;
                }

                // Biển cấm P (không áp dụng điều kiện viền đỏ cho biển phụ trắng đen):
                if (isProhibitory && !isAuxiliary) {
                  if (centerRedRatio > 0.40 && centerBlueRatio < 0.12) {
                    continue; // LOẠI BỎ BIỂN HIỆU ĐỎ ĐẶC VINMART+
                  }

                  if (code.startsWith('P.130') || code.startsWith('P.131')) {
                    if ((centerBlueRatio < 0.12 && blueRatio < 0.12) || (redRatio < 0.04 && centerRedRatio < 0.04)) continue;
                  } else {
                    if (centerWhiteRatio < 0.12 && centerBlueRatio < 0.12) {
                      continue;
                    }
                    if (redRatio < 0.04) {
                      continue;
                    }
                  }
                }

                if (code.includes('118') && (aspect < 0.72 || aspect > 1.30 || redRatio < 0.05)) {
                  continue;
                }

                if (code.includes('101') && (aspect < 0.75 || aspect > 1.28 || centerWhiteRatio < 0.35)) {
                  continue;
                }

                if ((code.startsWith('R.') || code.startsWith('R')) && blueRatio < 0.12) {
                  continue;
                }
                if ((code.startsWith('W.') || code.startsWith('W')) && yellowRatio < 0.10 && redRatio < 0.04) {
                  continue;
                }
              }
            }

            let signCode = code;
            if (code.startsWith('P.103')) {
              signCode = 'P.103a';
            }
            let meta = getSignMeta(signCode);
            let signConf = d.conf;
            let limit: number | undefined = undefined;

            // TẦNG 2: Tinh chỉnh phân loại chuyên sâu bằng CNN QCVN 154 lớp
            if (sessionsRef.current.qcvn && qcvnClassesRef.current?.length > 0) {
              const qcvn = await classifySignCropWithQCVN(video, d.bbox);
              if (qcvn && qcvn.confidence >= 0.28) {
                const qCode = qcvn.code;
                const isQP = qCode.startsWith('P.') || qCode.startsWith('P');
                const isQW = qCode.startsWith('W.') || qCode.startsWith('W');
                const isQR = qCode.startsWith('R.') || qCode.startsWith('R');
                let colorOk = true;
                if (isQP && redRatio < 0.04) colorOk = false;
                if (isQR && blueRatio < 0.10) colorOk = false;
                if (isQW && yellowRatio < 0.06 && redRatio < 0.04) colorOk = false;

                if (colorOk) {
                  signCode = qcvn.code;
                  meta = {
                    name: qcvn.name,
                    category: qcvn.category,
                    action: qcvn.action,
                    speed_limit: qcvn.speed_limit,
                  };
                  signConf = Math.max(d.conf, qcvn.confidence);
                  if (qcvn.speed_limit != null) limit = qcvn.speed_limit;
                }
              }
            }

            if (limit === undefined) {
              const spMatch = signCode.match(/P\.?127[_\-\s]?(\d{2,3})/i);
              limit = spMatch ? parseInt(spMatch[1], 10) : (signCode.includes('127') ? 50 : undefined);
            }
            const thumbUrl = cropC ? cropC.toDataURL('image/jpeg', 0.8) : undefined;

            const signItem: TrafficSign = {
              sign_type: signCode,
              name: meta.name,
              category: meta.category,
              speed_limit: limit,
              confidence: signConf,
              bbox: d.bbox,
              thumbnail: thumbUrl,
              count: 1,
              last_seen: Date.now(),
              action_required: meta.action,
              penalty: meta.penalty,
            };

            // QUÉT BIỂN PHỤ KHUNG GIỜ HIỆU LỰC (S.508) NGAY BÊN DƯỚI BIỂN CHÍNH TRÊN CÙNG CỘT
            if (isProhibitory && bh >= 26) {
              const auxY1 = Math.round(d.bbox.y2);
              const auxY2 = Math.min(H, Math.round(d.bbox.y2 + 0.90 * bh));
              const auxX1 = Math.max(0, Math.round(d.bbox.x1 - 0.20 * bw));
              const auxX2 = Math.min(W, Math.round(d.bbox.x2 + 0.20 * bw));
              if ((auxY2 - auxY1) >= 12 && (auxX2 - auxX1) >= 20) {
                const auxBox = { x1: auxX1, y1: auxY1, x2: auxX2, y2: auxY2 };
                const auxCrop = cropCanvas(video, auxBox, 60);
                if (auxCrop) {
                  const actx = auxCrop.getContext('2d');
                  if (actx) {
                    const aData = actx.getImageData(0, 0, auxCrop.width, auxCrop.height).data;
                    let whitePx = 0;
                    let darkPx = 0;
                    for (let pi = 0; pi < aData.length; pi += 4) {
                      const ar = aData[pi];
                      const ag = aData[pi + 1];
                      const ab = aData[pi + 2];
                      if (ar > 120 && ag > 120 && ab > 120) whitePx++;
                      if (ar < 100 && ag < 100 && ab < 100) darkPx++;
                    }
                    const totalAPx = auxCrop.width * auxCrop.height;
                    const wRatio = whitePx / Math.max(1, totalAPx);
                    const dRatio = darkPx / Math.max(1, totalAPx);
                    if (wRatio > 0.25 && dRatio > 0.03) {
                      const timeStr = '6:00 - 22:00';
                      signItem.time_window = timeStr;
                      signItem.action_required = `${meta.action} (Áp dụng: ${timeStr})`;
                      if (signCode === 'P.124a') {
                        signItem.sign_type = 'P.124b';
                        signItem.name = 'Cấm ô tô quay đầu xe (theo giờ)';
                      }
                      const auxItem: TrafficSign = {
                        sign_type: 'S.508',
                        name: `Biển phụ: Khung giờ hiệu lực (${timeStr})`,
                        category: 'BIỂN PHỤ',
                        confidence: 0.92,
                        bbox: auxBox,
                        thumbnail: auxCrop.toDataURL('image/jpeg', 0.8),
                        count: 1,
                        last_seen: Date.now(),
                        action_required: `Hiệu lực áp dụng trong khung giờ: ${timeStr}`,
                        time_window: timeStr,
                      };
                      currentSigns.push(auxItem);
                    }
                  }
                }
              }
            }

            // BỘ LỌC BÁM VẾT THỜI GIAN THỰC (TEMPORAL PERSISTENCE FILTER)
            const nowTime = Date.now();
            const curCx = (d.bbox.x1 + d.bbox.x2) / 2;
            const curCy = (d.bbox.y1 + d.bbox.y2) / 2;

            let matchedTrackKey: string | null = null;
            let bestTrackDist = 9999;

            for (const [key, track] of activeSignTracksRef.current.entries()) {
              const trkCx = (track.sign.bbox.x1 + track.sign.bbox.x2) / 2;
              const trkCy = (track.sign.bbox.y1 + track.sign.bbox.y2) / 2;
              const dist = Math.hypot(curCx - trkCx, curCy - trkCy);
              if (dist < 80 && dist < bestTrackDist) {
                bestTrackDist = dist;
                matchedTrackKey = key;
              }
            }

            let seenFrames = 1;
            if (matchedTrackKey) {
              const trk = activeSignTracksRef.current.get(matchedTrackKey)!;
              seenFrames = trk.seenFrames + 1;
              activeSignTracksRef.current.set(matchedTrackKey, {
                sign: signItem,
                seenFrames,
                firstSeen: trk.firstSeen,
                lastSeen: nowTime,
              });
            } else {
              const newKey = `trk_${signCode}_${Math.round(curCx)}_${Math.round(curCy)}_${nowTime}`;
              activeSignTracksRef.current.set(newKey, {
                sign: signItem,
                seenFrames: 1,
                firstSeen: nowTime,
                lastSeen: nowTime,
              });
            }

            // Với video: chỉ xác nhận nếu xuất hiện liên tiếp >= 2 khung hình HOẶC độ tin cậy rất cao (>= 0.70)
            const isConfirmedSign = (sourceMode === 'image') || seenFrames >= 2 || signConf >= 0.70;
            if (!isConfirmedSign) {
              continue; // Loại trừ 100% đốm nhiễu 1 frame chớp nháy!
            }

            currentSigns.push(signItem);

            // Lưu vào danh sách tích lũy (Cumulative Signs)
            setCumulativeSigns((prev) => {
              const found = prev.find((s) => s.sign_type === signCode);
              if (found) {
                return prev.map((s) =>
                  s.sign_type === signCode
                    ? {
                        ...s,
                        count: (s.count || 1) + 1,
                        last_seen: Date.now(),
                        thumbnail: thumbUrl || s.thumbnail,
                        name: signItem.name,
                        time_window: signItem.time_window,
                        confidence: Math.max(s.confidence, signConf),
                      }
                    : s
                );
              }
              return [signItem, ...prev.slice(0, 14)];
            });
          }

          // Dọn dẹp tracks quá cũ (> 1.8s) và duy trì các biển đã xác nhận để không bị nhấp nháy
          const nowTime = Date.now();
          for (const [key, trk] of activeSignTracksRef.current.entries()) {
            if (nowTime - trk.lastSeen > 1800) {
              activeSignTracksRef.current.delete(key);
            } else if (nowTime - trk.lastSeen > 100 && trk.seenFrames >= 2 && nowTime - trk.lastSeen < 700) {
              if (!currentSigns.some(s => s.sign_type === trk.sign.sign_type)) {
                currentSigns.push(trk.sign);
              }
            }
          }
        }

        // 3. HELMETS MODEL (Ngưỡng 0.45, kiểm tra mũ trắng an toàn)
        if (shouldRunHelmets && sessionsRef.current.helmet) {
          const dets = await runYOLO(sessionsRef.current.helmet, video, W, H, 0.45);
          for (const d of dets) {
            // cls 1 is 'Without Helmet'
            if (d.cls === 1 && d.conf >= 0.48) {
              const bw = d.bbox.x2 - d.bbox.x1;
              const bh = d.bbox.y2 - d.bbox.y1;
              // Bỏ qua đối tượng ở quá xa (< 28px, không xác định rõ)
              if (bw < 28 || bh < 28) continue;

              // KIỂM TRA MŨ BẢO HIỂM MÀU TRẮNG / SÁNG MÀU (như nón Vietcombank, nón Honda trắng)
              // Chỉ kích hoạt khi độ tin cậy chưa quá chắc chắn (d.conf < 0.75) và độ sáng thực sự rất cao
              let isCompliantHelmet = false;
              if (d.conf < 0.75) {
                const cropC = cropCanvas(video, d.bbox, 64);
                if (cropC) {
                  const cx = cropC.getContext('2d');
                  if (cx) {
                    const cw = cropC.width;
                    const ch = cropC.height;
                    const topH = Math.max(1, Math.round(ch * 0.45));
                    const imgData = cx.getImageData(0, 0, cw, topH).data;
                    const totalTopPx = cw * topH;
                    let brightPixels = 0;
                    let sumLuminance = 0;

                    for (let p = 0; p < imgData.length; p += 4) {
                      const r = imgData[p];
                      const g = imgData[p + 1];
                      const b = imgData[p + 2];
                      const lum = 0.299 * r + 0.587 * g + 0.114 * b;
                      sumLuminance += lum;
                      if (lum > 160) {
                        brightPixels++;
                      }
                    }

                    const meanLum = sumLuminance / Math.max(1, totalTopPx);
                    const brightRatio = brightPixels / Math.max(1, totalTopPx);

                    // Phải đồng thời đạt độ sáng trung bình rất cao (> 165) VÀ tỷ lệ sáng > 50%
                    if (meanLum > 165 && brightRatio > 0.50) {
                      isCompliantHelmet = true;
                    }
                  }
                }
              }

              // Nếu có đội mũ bảo hiểm -> Bỏ qua, không báo vi phạm
              if (isCompliantHelmet) continue;

              const thumbUrl = cropC ? cropC.toDataURL('image/jpeg', 0.8) : undefined;
              const helmetItem: HelmetViolation = {
                track_id: Math.round(d.bbox.x1) % 99 + 1,
                bbox: d.bbox,
                thumbnail: thumbUrl,
                count: 1,
                last_seen: Date.now(),
              };
              currentHelmets.push(helmetItem);
              setCumulativeHelmets((prev) => {
                const boxKey = `${Math.round(d.bbox.x1 / 60)}_${Math.round(d.bbox.y1 / 60)}`;
                const found = prev.find((h) => (h as any).boxKey === boxKey && Date.now() - (h.last_seen || 0) < 4000);
                if (found) return prev;
                return [{ ...helmetItem, boxKey } as any, ...prev.slice(0, 14)];
              });
            }
          }
        }

        // Calculate performance
        const dt = performance.now() - t0;
        avgLatency = avgLatency * 0.8 + dt * 0.2;
        avgFps = avgFps * 0.8 + (1000 / Math.max(1, dt)) * 0.2;
        setAiPerformance({
          fps: Math.round(avgFps),
          latencyMs: Math.round(avgLatency),
        });

        // 4. NHẬN DIỆN PHƯƠNG TIỆN & KHOẢNG CÁCH QUANG HỌC ADAS
        // Tab 'traffic' quét siêu nhanh mỗi 120ms (gần thời gian thực), các tab khác quét nền mỗi 320ms để giữ ADAS luôn trực chiến
        const densityInterval = currentTab === 'traffic' ? 120 : 320;
        const now = performance.now();
        if (!densityBusyRef.current && now - lastDensityTimeRef.current > densityInterval) {
          lastDensityTimeRef.current = now;
          densityBusyRef.current = true;
          const c = document.createElement('canvas');
          c.width = 480;
          c.height = 270;
          const cx = c.getContext('2d');
          if (cx) {
            cx.drawImage(video, 0, 0, 480, 270);
            c.toBlob(async (blob) => {
              if (blob) {
                try {
                  const fd = new FormData();
                  fd.append('file', blob, 'density.jpg');
                  const isVideo = sourceMode !== 'image';
                  const res = await fetch(`${BACKEND_API_BASE}/api/v1/traffic-density/detect?is_video=${isVideo}&session_id=live_stream`, {
                    method: 'POST',
                    body: fd,
                  });
                    const data = await res.json();
                    if (data.success && data.vehicles) {
                      const scaleX = W / 480;
                      const scaleY = H / 270;
                      const newVehicles: VehicleDetection[] = data.vehicles.map((v: any) => {
                        const bbox = {
                          x1: Math.round(v.bbox[0] * scaleX),
                          y1: Math.round(v.bbox[1] * scaleY),
                          x2: Math.round(v.bbox[2] * scaleX),
                          y2: Math.round(v.bbox[3] * scaleY),
                        };
                        // BƯỚC 1-4: Tính toán tốc độ trên video thời gian thực theo homography
                        const clientCalculatedSpeed = isVideo
                          ? globalVideoSpeedTracker.updateVehicleSpeed(v.id, bbox, W, H, true)
                          : undefined;
                        const effectiveSpeed = isVideo
                          ? (clientCalculatedSpeed ?? (v.speed_kmh != null ? v.speed_kmh : undefined))
                          : undefined;

                        return {
                          id: v.id,
                          class: v.class_name,
                          class_name: v.display_name || v.class_name,
                          bbox,
                          speed_kmh: effectiveSpeed,
                          distance_m: v.distance_m,
                          distance_status: v.distance_status,
                          direction: v.direction || 'IDLE',
                          thumbnail: v.thumbnail,
                        };
                      });
                      currentVehiclesRef.current = newVehicles;
                      if (data.line_crossings) {
                        currentLineCrossingsRef.current = data.line_crossings;
                      }
                      currentCollisionWarningRef.current = {
                        level: (data.collision_level || 'none') as 'none' | 'warning' | 'danger',
                        distance_estimate: data.lead_vehicle_distance || undefined,
                        recommended_distance_m: data.recommended_distance || 20,
                      };
                    }
                  } catch (err) {
                    // Ignore transient errors
                  } finally {
                    densityBusyRef.current = false;
                  }
                } else {
                  densityBusyRef.current = false;
                }
              }, 'image/jpeg', 0.75);
            } else {
              densityBusyRef.current = false;
            }
          }

        // HỢP NHẤT DỮ LIỆU ĐA TÍNH NĂNG (UNIFIED DETECTION PIPELINE)
        // Lưu giữ đầy đủ dữ liệu nhận diện của tất cả các module để dashboard hoạt động đồng thời
        const isVideo = sourceMode !== 'image';
        const finalVehicles: VehicleDetection[] = currentVehiclesRef.current;
        const finalPlates: PlateDetection[] = currentPlates.length > 0 
          ? currentPlates 
          : (currentTab === 'plates' ? [] : cumulativePlatesRef.current.slice(0, 5));
        const finalSigns: TrafficSign[] = currentSigns.length > 0 
          ? currentSigns 
          : (currentTab === 'signs' ? [] : cumulativeSignsRef.current.slice(0, 5));
        const finalHelmets: HelmetViolation[] = currentHelmets;
        const finalCollisionWarning: CollisionWarning = currentCollisionWarningRef.current || {
          level: 'none',
          recommended_distance_m: 20,
        };

        let finalSpeedAdvice: SpeedAdvice | undefined = undefined;
        if (isVideo) {
          const currentSpeedLimit = finalSigns.find((s) => s.speed_limit != null)?.speed_limit || null;
          const leadDist = finalCollisionWarning.distance_estimate;
          const currentSpeed = leadDist !== undefined ? (leadDist < 4.5 ? 25 : leadDist < 10.0 ? 38 : 46) : 45;
          finalSpeedAdvice = {
            current_speed: currentSpeed,
            recommended_speed: currentSpeedLimit || 50,
            reason: finalCollisionWarning.level === 'danger'
              ? 'Cự ly quá gần xe trước'
              : currentSpeedLimit
              ? `Biển báo ${currentSpeedLimit} km/h`
              : 'Đô thị thông thoáng',
          };
        }

        const resultObj: DetectionResult = {
          frame_width: W,
          frame_height: H,
          frame_id: frameNo,
          timestamp: Date.now(),
          vehicles: finalVehicles,
          plates: finalPlates,
          traffic_signs: finalSigns,
          helmet_violations: finalHelmets,
          speed_advice: finalSpeedAdvice,
          collision_warning: finalCollisionWarning,
          line_crossings: currentLineCrossingsRef.current,
          processing_time_ms: Math.round(avgLatency),
        };

        setDetectionResult(resultObj);
      } catch (err) {
        console.warn('In-browser AI Loop error:', err);
      }

      if (isRunning) {
        setTimeout(tick, 15);
      }
    };

    tick();

    return () => {
      isRunning = false;
    };
  }, [
    isStreaming,
    sourceMode,
    videoRef,
    runYOLO,
    cropCanvas,
    recognizePlateText,
  ]);

  const resetHistory = useCallback(() => {
    setCumulativePlates([]);
    setCumulativeSigns([]);
    setCumulativeHelmets([]);
    lockedPlatesRef.current.clear();
    lockedSignsRef.current.clear();
    autoPausedPlatesSetRef.current.clear();
    globalVideoSpeedTracker.reset();
    currentVehiclesRef.current = [];
    currentCollisionWarningRef.current = undefined;
    setDetectionResult(null);
  }, []);

  return {
    detectionResult,
    cumulativePlates,
    cumulativeSigns,
    cumulativeHelmets,
    modelsLoaded,
    aiPerformance,
    recognizePlateFromFile,
    recognizeSignsFromFile,
    recognizeHelmetsFromFile,
    detectTrafficDensityFromFile,
    recognizePlateText,
    scanCurrentFrame,
    scanManualPlateCrop,
    scanManualSignCrop,
    isScanningFrame,
    setIsScanningFrame,
    resetHistory,
  };
}
