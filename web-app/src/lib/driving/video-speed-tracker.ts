/**
 * video-speed-tracker.ts
 * ----------------------
 * Hệ thống đo vận tốc phương tiện trên VIDEO theo phối cảnh mặt đường (Road Homography).
 * Tuân thủ quy chuẩn 4 bước:
 * 1. Tracking ID cố định qua các khung hình video.
 * 2. Điểm đại diện: Điểm giữa cạnh dưới bounding box ((x1 + x2)/2, y2) nơi bánh xe tiếp xúc mặt đường.
 * 3. Chuyển pixel sang mét bằng ma trận chiếu phối cảnh (Homography).
 * 4. Tính vận tốc = khoảng cách mét / thời gian (cửa sổ 0.5s - 1.0s) và làm mượt chống nhiễu.
 *
 * ĐẶC BIỆT: CHỈ TÍNH VẬN TỐC TRÊN VIDEO! Trên ảnh tĩnh, hàm trả về undefined để không hiển thị vận tốc giả.
 */

export interface TrackPoint {
  timeSec: number;
  xMeters: number;
  yMeters: number;
}

export class VideoSpeedTracker {
  private historyMap: Map<number, TrackPoint[]> = new Map();
  private smoothedSpeedMap: Map<number, number> = new Map();
  private lastSeenMap: Map<number, number> = new Map();
  private readonly minWindowSec = 0.35;
  private readonly maxWindowSec = 1.0;

  /**
   * Chuyển đổi tọa độ pixel (x, y) sang tọa độ mặt đường thực tế (X, Y tính bằng mét).
   * Sử dụng ma trận phối cảnh chuẩn hóa cho góc nhìn camera hành trình xe (Dashcam/Road Camera).
   */
  private toMeters(pixelX: number, pixelY: number, frameWidth: number, frameHeight: number): { x: number; y: number } {
    const W = Math.max(1, frameWidth);
    const H = Math.max(1, frameHeight);

    // Tọa độ chuẩn hóa trong [0, 1]
    const u = Math.min(1.0, Math.max(0.0, pixelX / W));
    const v = Math.min(1.0, Math.max(0.0, pixelY / H));

    // Hệ số ma trận Homography chuẩn hóa (tương ứng làn đường rộng 3.5m, tầm nhìn 3.5m - 32m)
    const wPrime = -3.77049197 * v + 1.0;
    if (Math.abs(wPrime) < 1e-6) {
      return { x: 0, y: 35.0 };
    }

    const xMeters = (-25.81967363 * u + 12.90983638) / wPrime;
    const yMeters = (42.86885807 * v - 49.76230065) / wPrime;

    return {
      x: xMeters,
      y: Math.max(1.0, yMeters),
    };
  }

  /**
   * Cập nhật vị trí của phương tiện trên video và tính vận tốc (km/h).
   * @param isVideo - Cờ xác định có phải đang chạy video không. Nếu là ảnh tĩnh (false) -> LUÔN TRẢ VỀ undefined!
   */
  public updateVehicleSpeed(
    vehicleId: number,
    bbox: { x1: number; y1: number; x2: number; y2: number },
    frameWidth: number,
    frameHeight: number,
    isVideo: boolean = true,
    timestampSec?: number
  ): number | undefined {
    // 1. TUYỆT ĐỐI KHÔNG TÍNH TỐC ĐỘ TRÊN ẢNH TĨNH!
    if (!isVideo) {
      return undefined;
    }

    const now = timestampSec !== undefined ? timestampSec : performance.now() / 1000.0;
    this.lastSeenMap.set(vehicleId, now);

    // 2. Điểm đại diện: Điểm giữa cạnh dưới (tiếp xúc mặt đường)
    const bottomCenterX = (bbox.x1 + bbox.x2) / 2.0;
    const bottomCenterY = bbox.y2;

    // 3. Đổi pixel sang mét
    const posMeters = this.toMeters(bottomCenterX, bottomCenterY, frameWidth, frameHeight);

    if (!this.historyMap.has(vehicleId)) {
      this.historyMap.set(vehicleId, []);
    }
    const history = this.historyMap.get(vehicleId)!;
    history.push({
      timeSec: now,
      xMeters: posMeters.x,
      yMeters: posMeters.y,
    });

    // Giữ lịch sử trong vòng 1.5 giây
    while (history.length > 2 && now - history[0].timeSec > 1.5) {
      history.shift();
    }

    // Cần ít nhất 2 mẫu và khoảng thời gian >= 0.35s để loại trừ nhiễu rung lắc khung hình
    if (history.length < 2) {
      return this.smoothedSpeedMap.get(vehicleId);
    }

    // Tìm mẫu trong cửa sổ [now - minWindowSec, now]
    let basePoint = history[0];
    for (let i = 0; i < history.length; i++) {
      if (now - history[i].timeSec >= this.minWindowSec) {
        basePoint = history[i];
        break;
      }
    }

    const dt = now - basePoint.timeSec;
    if (dt < this.minWindowSec) {
      return this.smoothedSpeedMap.get(vehicleId);
    }

    // 4. Tính vận tốc = khoảng cách / thời gian
    const dx = posMeters.x - basePoint.xMeters;
    const dy = posMeters.y - basePoint.yMeters;
    const distanceM = Math.hypot(dx, dy);

    const vMs = distanceM / dt;
    const rawSpeedKmh = vMs * 3.6;

    let currentSpeed: number;
    // Deadband: Nếu xe di chuyển < 0.4m trong cửa sổ thời gian hoặc v < 2.5 km/h -> Đứng yên (0 km/h)
    if (rawSpeedKmh < 2.5 || distanceM < 0.40) {
      currentSpeed = 0.0;
    } else {
      // Giới hạn vận tốc đô thị hợp lý (tối đa 110 km/h)
      currentSpeed = Math.min(110.0, rawSpeedKmh);
    }

    // Làm mượt theo trung bình trượt trọng số (EMA)
    const prevSmoothed = this.smoothedSpeedMap.get(vehicleId);
    const smoothed = prevSmoothed === undefined ? currentSpeed : 0.65 * prevSmoothed + 0.35 * currentSpeed;
    const rounded = Math.round(smoothed);

    this.smoothedSpeedMap.set(vehicleId, rounded);
    return rounded;
  }

  /**
   * Xóa lịch sử khi chuyển video hoặc dừng luồng.
   */
  public reset(): void {
    this.historyMap.clear();
    this.smoothedSpeedMap.clear();
    this.lastSeenMap.clear();
  }

  /**
   * Dọn dẹp các ID xe đã biến mất quá 3 giây.
   */
  public pruneStaleTracks(): void {
    const now = performance.now() / 1000.0;
    for (const [id, lastTime] of this.lastSeenMap.entries()) {
      if (now - lastTime > 3.0) {
        this.historyMap.delete(id);
        this.smoothedSpeedMap.delete(id);
        this.lastSeenMap.delete(id);
      }
    }
  }
}

// Singleton tracker instance cho toàn ứng dụng
export const globalVideoSpeedTracker = new VideoSpeedTracker();
