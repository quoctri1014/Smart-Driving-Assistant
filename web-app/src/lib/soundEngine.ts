/**
 * soundEngine.ts
 * --------------
 * Hệ thống âm thanh cảnh báo & giọng đọc tiếng Việt cho Web Dashboard:
 * 1. Web Audio API: Phát âm còi khẩn cấp (Siren/Alarm) hoặc Chime (Warning).
 * 2. Web Speech API: Đọc câu nhắc tiếng Việt (vi-VN) tự nhiên, chống GC bug trình duyệt.
 * 3. Hỗ trợ Mute / Unmute, Test voice, và mở khóa AudioContext tự động khi tương tác.
 */

class SoundEngine {
  private audioCtx: AudioContext | null = null;
  private isMuted: boolean = false;
  private volume: number = 0.9;
  private lastSpokenText: string = "";
  private lastSpokenTime: number = 0;
  private activeUtterances: Set<SpeechSynthesisUtterance> = new Set();
  private cachedVoices: SpeechSynthesisVoice[] = [];
  private isInitialized: boolean = false;

  constructor() {
    if (typeof window !== 'undefined') {
      this.initVoices();
    }
  }

  private initVoices() {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;

    const loadVoices = () => {
      try {
        const voices = window.speechSynthesis.getVoices();
        if (voices && voices.length > 0) {
          this.cachedVoices = voices;
          this.isInitialized = true;
        }
      } catch {
        // Ignore voice loading error
      }
    };

    loadVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }

  public unlockAudio(): boolean {
    if (typeof window === 'undefined') return false;

    // 1. Mở khóa AudioContext
    try {
      const ctx = this.getAudioContext();
      if (ctx && ctx.state === 'suspended') {
        ctx.resume();
      }
    } catch {
      // Ignore
    }

    // 2. Mở khóa SpeechSynthesis
    try {
      if ('speechSynthesis' in window) {
        if (window.speechSynthesis.paused) {
          window.speechSynthesis.resume();
        }
        this.initVoices();
      }
    } catch {
      // Ignore
    }

    return true;
  }

  private getAudioContext(): AudioContext | null {
    if (typeof window === 'undefined') return null;
    if (!this.audioCtx) {
      const AudioContextClass =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioContextClass) {
        this.audioCtx = new AudioContextClass();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    return this.audioCtx;
  }

  public setMuted(muted: boolean) {
    this.isMuted = muted;
    if (muted && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch {
        // Ignore
      }
    }
  }

  public getIsMuted(): boolean {
    return this.isMuted;
  }

  public toggleMuted(): boolean {
    this.unlockAudio();
    this.setMuted(!this.isMuted);
    return this.isMuted;
  }

  public setVolume(vol: number) {
    this.volume = Math.max(0, Math.min(1, vol));
  }

  private emitTone(ctx: AudioContext, soundType: 'alarm_critical' | 'chime') {
    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.connect(gain);
      gain.connect(ctx.destination);

      if (soundType === 'alarm_critical') {
        // Còi báo động khẩn cấp hai tần số cao dứt khoát
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.linearRampToValueAtTime(1320, now + 0.15);
        osc.frequency.linearRampToValueAtTime(880, now + 0.3);
        gain.gain.setValueAtTime(this.volume * 0.6, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.4);
        osc.start(now);
        osc.stop(now + 0.4);
      } else {
        // Chime hai nốt nhẹ nhàng
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, now); // D5
        osc.frequency.setValueAtTime(880, now + 0.1); // A5
        gain.gain.setValueAtTime(this.volume * 0.5, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
        osc.start(now);
        osc.stop(now + 0.35);
      }
    } catch {
      // Ignore web audio exceptions
    }
  }

  public playSound(soundType: 'alarm_critical' | 'chime') {
    if (this.isMuted) return;
    this.unlockAudio();

    const ctx = this.getAudioContext();
    if (!ctx) return;

    if (ctx.state === 'suspended') {
      ctx.resume().then(() => {
        this.emitTone(ctx, soundType);
      }).catch(() => {});
      return;
    }
    this.emitTone(ctx, soundType);
  }

  public speak(
    text: string,
    priority: 'normal' | 'critical' = 'normal',
    bypassCooldown: boolean = false
  ) {
    if (this.isMuted || !text) return;
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;

    this.unlockAudio();

    const now = Date.now();
    if (!bypassCooldown) {
      // Chống lặp cùng câu trong 4.0 giây
      if (text === this.lastSpokenText && (now - this.lastSpokenTime) < 4000) {
        return;
      }
      // Câu khẩn cấp cũng cần ít nhất 2.2 giây giữa 2 lần phát để không bị nuốt chữ/ngắt dồn dập
      if (priority === 'critical' && (now - this.lastSpokenTime) < 2200) {
        return;
      }
      // Khoảng cách tối thiểu giữa các câu thông thường là 2.5 giây
      if ((now - this.lastSpokenTime) < 2500 && priority !== 'critical') {
        return;
      }
    }

    try {
      if (priority === 'critical' && window.speechSynthesis.speaking) {
        // Chỉ ngắt nếu câu trước đó đã phát trên 1.5 giây hoặc là câu bình thường
        if ((now - this.lastSpokenTime) > 1500) {
          window.speechSynthesis.cancel();
        }
      }

      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05; // Đọc nhanh gọn, dứt khoát
      utterance.pitch = 1.0;
      utterance.volume = this.volume;

      // Tìm giọng tiếng Việt nếu có trong trình duyệt
      const voices =
        this.cachedVoices.length > 0 ? this.cachedVoices : window.speechSynthesis.getVoices();
      const viVoice = voices.find(
        (v) =>
          v.lang.toLowerCase().replace('_', '-').includes('vi-vn') ||
          v.lang.toLowerCase().startsWith('vi') ||
          v.name.toLowerCase().includes('vietnam') ||
          v.name.toLowerCase().includes('tiếng việt')
      );

      if (viVoice) {
        utterance.voice = viVoice;
        utterance.lang = viVoice.lang;
      } else {
        // Giữ lang là vi-VN để Chrome tự động kích hoạt Cloud Vietnamese TTS
        utterance.lang = 'vi-VN';
      }

      // Giữ tham chiếu để tránh Chrome Garbage Collection hủy ngang utterance
      this.activeUtterances.add(utterance);
      utterance.onend = () => {
        this.activeUtterances.delete(utterance);
      };
      utterance.onerror = () => {
        this.activeUtterances.delete(utterance);
      };

      this.lastSpokenText = text;
      this.lastSpokenTime = now;

      window.speechSynthesis.speak(utterance);
    } catch {
      // Fallback: Nếu Web Speech API bị lỗi trên trình duyệt, vẫn phát âm còi báo
      this.playSound(priority === 'critical' ? 'alarm_critical' : 'chime');
    }
  }

  public testVoice() {
    this.isMuted = false;
    this.unlockAudio();
    this.playSound('chime');
    setTimeout(() => {
      this.speak('Hệ thống cảnh báo giọng nói tiếng Việt đã sẵn sàng!', 'normal', true);
    }, 250);
  }

  public handleDecisionAudio(soundAlert?: string | null, speechPrompt?: string | null) {
    if (soundAlert === 'alarm_critical') {
      this.playSound('alarm_critical');
      if (speechPrompt) {
        setTimeout(() => this.speak(speechPrompt, 'critical'), 250);
      }
    } else if (soundAlert === 'chime') {
      this.playSound('chime');
      if (speechPrompt) {
        setTimeout(() => this.speak(speechPrompt, 'normal'), 200);
      }
    } else if (speechPrompt) {
      this.speak(speechPrompt, 'normal');
    }
  }

  // --- 6 LOẠI CẢNH BÁO CHUẨN ĐẶC TẢ BẢNG 6.1 BÁO CÁO CHUYÊN ĐỀ ---
  public playFCWAlert() {
    this.playSound('alarm_critical');
    setTimeout(() => this.speak('Nguy hiểm: Giữ khoảng cách an toàn!', 'critical'), 200);
  }

  public playDrowsinessAlert() {
    this.playSound('alarm_critical');
    setTimeout(() => this.speak('Cảnh báo: Tài xế đang buồn ngủ, vui lòng nghỉ ngơi!', 'critical'), 200);
  }

  public playOverspeedAlert() {
    this.playSound('chime');
    setTimeout(() => this.speak('Chú ý: Giảm tốc độ xe!', 'normal'), 200);
  }

  public playLaneDepartureAlert() {
    this.playSound('chime');
    setTimeout(() => this.speak('Nhắc nhở: Xe đang chệch làn đường!', 'normal'), 200);
  }

  public playSeatbeltAlert() {
    this.playSound('chime');
    setTimeout(() => this.speak('Nhắc nhở: Vui lòng thắt dây an toàn trước khi chạy!', 'normal'), 200);
  }

  public playFatigueAlert() {
    this.playSound('chime');
    setTimeout(() => this.speak('Nhắc nhở: Quý khách đã lái xe liên tục 4 giờ, vui lòng dừng nghỉ!', 'normal'), 200);
  }
}

export const soundEngine = new SoundEngine();

